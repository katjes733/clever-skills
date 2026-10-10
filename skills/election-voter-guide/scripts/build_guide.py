#!/usr/bin/env python3
"""Build and validate the voter-guide page.

Usage:
    python3 build_guide.py DATA.json OUT.html          # validate + build
    python3 build_guide.py --sample OUT.html           # build from assets/sample-guide.json
    python3 build_guide.py DATA.json --check           # validate only

The page is rendered entirely from the JSON data, so a guide is produced by filling
the data file (see assets/sample-guide.json for the shape) and running this script.

Exit status: 0 = built (warnings may be printed), 1 = validation errors, 2 = usage/IO error.
"""
import json
import re
import sys
from html import escape
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
TEMPLATE = ASSETS / "voter-guide-template.html"
SAMPLE = ASSETS / "sample-guide.json"

STAGES = {"ballot", "profile", "guide"}
TABS = {"overview", "ballot", "profile", "guide", "measures", "cheat", "sources"}
RATINGS = {"strong", "good", "mixed", "weak", "poor", "unknown", "na"}
LEGACY_RATINGS = {"moderate": "mixed"}
CONFIDENCE = {"very_high", "high", "medium", "low", "very_low"}
CONF_ORDER = ["very_low", "low", "medium", "high", "very_high"]
DECISIONS = {"clear", "lean", "slight", "toss_up"}
# Source kinds for the completeness inventory. The first group is address-free and official: a county-wide
# candidate list or sample ballots need no street address, so use them first.
OFFICIAL_LIST_KINDS = {"county_candidate_list", "state_candidate_list", "sample_ballot", "voter_sample_ballot", "voter_pamphlet", "measure_list"}
SOURCE_KINDS = OFFICIAL_LIST_KINDS | {"official_other", "aggregator", "news"}
DEPTH = {"deep", "moderate", "thin"}
LEAN = {"yes", "no", "undecided"}
BASIS = {"record", "statement", "party_platform"}
STATUS = {"verified", "unverified"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def err(self, where, msg):
        self.errors.append(f"ERROR   {where}: {msg}")

    def warn(self, where, msg):
        self.warnings.append(f"WARNING {where}: {msg}")


def is_http_url(value):
    try:
        p = urlparse(value)
    except Exception:
        return False
    return p.scheme in ("http", "https") and bool(p.netloc)


def check_url(rep, where, value, required=False):
    if value in (None, ""):
        if required:
            rep.err(where, "URL is required")
        return
    if not isinstance(value, str) or not is_http_url(value):
        rep.err(where, f"URL must start with http:// or https:// (got {value!r})")


def check_sources(rep, where, sources, required):
    if not sources:
        (rep.err if required else rep.warn)(where, "no sources listed; every substantive claim needs a source")
        return
    for i, s in enumerate(sources):
        w = f"{where}.sources[{i}]"
        if not isinstance(s, dict):
            rep.err(w, "must be an object with title, url, retrieved")
            continue
        if not s.get("title"):
            rep.warn(w, "missing title")
        check_url(rep, w + ".url", s.get("url"), required=True)
        r = s.get("retrieved")
        if not r:
            rep.warn(w, "missing retrieved date (YYYY-MM-DD)")
        elif not DATE_RE.match(r):
            rep.err(w, f"retrieved must be YYYY-MM-DD (got {r!r})")


def check_rating(rep, where, value, allow_empty=False):
    if value in (None, "") and allow_empty:
        return
    if value not in RATINGS and value not in LEGACY_RATINGS:
        rep.err(where, f"rating must be one of {sorted(RATINGS)} (got {value!r})")


def check_completeness(rep, data):
    """The ballot inventory must come from authoritative sources, and every inventory item must appear in the guide.

    This is the completeness gate: it cannot be satisfied by asking the voter, and it cannot be satisfied by
    sampling claims that are already in the guide (which would never reveal what is missing).
    """
    comp = data.get("completeness")
    stage = (data.get("meta") or {}).get("stage")
    if not isinstance(comp, dict):
        rep.err("completeness", "missing: build the ballot inventory from official sources before the guide (sources, expected, independent_check)")
        return
    srcs = comp.get("sources") or []
    if not srcs:
        rep.err("completeness.sources", "list the official sources the inventory was built from")
    for i, sc in enumerate(srcs):
        w = f"completeness.sources[{i}]"
        if not sc.get("label"):
            rep.err(w, "label required")
        check_url(rep, w + ".url", sc.get("url"), required=sc.get("kind") != "voter_sample_ballot")
        if sc.get("kind") not in SOURCE_KINDS:
            rep.err(w, f"kind must be one of {sorted(SOURCE_KINDS)}")
        if not sc.get("retrieved"):
            rep.warn(w, "add a retrieved date")
    if srcs and not any(sc.get("kind") in OFFICIAL_LIST_KINDS for sc in srcs):
        rep.warn("completeness.sources", "no official candidate list, sample ballot, or voter pamphlet among the sources; a county candidate list (often a PDF) needs no street address, so look for it")
    if not comp.get("checked_on"):
        rep.warn("completeness.checked_on", "add the date the inventory was checked")

    race_ids = {r.get("id") for r in data.get("races") or []}
    meas_ids = {m.get("id") for m in data.get("measures") or []}
    expected = comp.get("expected") or []
    if not expected:
        rep.err("completeness.expected", "list every office and measure the voter could see, from the official sources, before listing candidates")
    exp_ids = set()
    for i, e in enumerate(expected):
        w = f"completeness.expected[{i}]"
        if not e.get("id") or not e.get("label"):
            rep.err(w, "id and label required")
            continue
        if e.get("type") not in ("race", "measure"):
            rep.err(w, "type must be 'race' or 'measure' (judicial retention counts as a measure)")
        exp_ids.add(e["id"])
        pool = race_ids if e.get("type") == "race" else meas_ids
        if e["id"] not in pool:
            rep.err(w, f"inventory item {e['label']!r} ({e['id']}) is not in the guide: add it, or move it to completeness.unresolved with the reason")
    for rid in sorted(x for x in (race_ids | meas_ids) if x and x not in exp_ids):
        rep.warn("completeness", f"{rid!r} is in the guide but not in the inventory; add it to completeness.expected with its source, or remove it")
    for u in comp.get("unresolved") or []:
        rep.warn("completeness.unresolved", f"not confirmed: {u.get('item', u) if isinstance(u, dict) else u}")
    checked_levels = set(comp.get("levels_checked") or [])
    if checked_levels:
        for lv in sorted({x.get("level") for x in (data.get("races") or []) + (data.get("measures") or []) if x.get("level")} - checked_levels):
            rep.warn("completeness.levels_checked", f"guide has {lv!r} items but that level is not listed as checked")
    else:
        rep.warn("completeness.levels_checked", "list the levels you checked (federal, state, county, municipal, school and special districts, judges)")
    ic = comp.get("independent_check")
    if not isinstance(ic, dict):
        (rep.err if stage == "guide" else rep.warn)("completeness.independent_check", "run the independent (blind) completeness check and record it, or record why it was skipped")
    elif not ic.get("done") and not ic.get("skipped_reason"):
        (rep.err if stage == "guide" else rep.warn)("completeness.independent_check", "done is false: run the blind completeness check or give skipped_reason")
    elif ic.get("skipped_reason") and not ic.get("done"):
        rep.warn("completeness.independent_check", f"independent check skipped: {ic['skipped_reason']}; the page will say so")


def validate(data):
    rep = Report()
    if not isinstance(data, dict):
        rep.err("root", "data must be a JSON object")
        return rep

    meta = data.get("meta") or {}
    for k in ("title", "election_name", "election_date", "jurisdiction", "generated", "stage"):
        if not meta.get(k):
            rep.err(f"meta.{k}", "required")
    for k in ("election_date", "generated"):
        if meta.get(k) and not DATE_RE.match(str(meta[k])):
            rep.err(f"meta.{k}", f"must be YYYY-MM-DD (got {meta[k]!r})")
    stage = meta.get("stage")
    if stage and stage not in STAGES:
        rep.err("meta.stage", f"must be one of {sorted(STAGES)}")
    if meta.get("default_tab") and meta["default_tab"] not in TABS:
        rep.err("meta.default_tab", f"must be one of {sorted(TABS)}")
    title = str(meta.get("title", ""))
    if len(title.split()) > 5:
        rep.warn("meta.title", "keep the title to a short name (about 2-4 words); put detail in the artifact description")

    if not data.get("election"):
        rep.warn("election", "missing election type/summary")

    for i, t in enumerate(data.get("timeline") or []):
        w = f"timeline[{i}]"
        if not t.get("label"):
            rep.err(w, "label required")
        if t.get("date") and not DATE_RE.match(t["date"]):
            rep.err(w, "date must be YYYY-MM-DD (use date_text for free text)")
        if t.get("end_date"):
            if not DATE_RE.match(t["end_date"]):
                rep.err(w, "end_date must be YYYY-MM-DD")
            elif not t.get("date"):
                rep.err(w, "end_date needs a start date")
            elif t["end_date"] < t["date"]:
                rep.err(w, "end_date is before date")
        if t.get("status") == "unverified":
            rep.warn(w, f"'{t.get('label')}' is unverified; confirm with the official page or tell the voter")
        if not t.get("date") and not t.get("date_text"):
            rep.warn(w, "no date or date_text")
        check_url(rep, w + ".url", t.get("url"))
    for i, r in enumerate(data.get("rules") or []):
        check_url(rep, f"rules[{i}].url", r.get("url"))

    races = data.get("races") or []
    measures = data.get("measures") or []
    guide_stage = stage == "guide"
    if not races and not measures:
        rep.warn("races", "no races or measures yet")

    seen_ids = set()
    for ri, r in enumerate(races):
        w = f"races[{ri}]({r.get('office', '?')})"
        rid = r.get("id")
        if not rid:
            rep.err(w, "id required")
        elif rid in seen_ids:
            rep.err(w, f"duplicate id {rid!r}")
        seen_ids.add(rid)
        for k in ("level", "office"):
            if not r.get(k):
                rep.err(w, f"{k} required")
        if r.get("status") and r["status"] not in STATUS:
            rep.err(w, f"status must be one of {sorted(STATUS)}")
        if not r.get("status"):
            rep.warn(w, "set status to verified or unverified")
        elif r["status"] == "unverified":
            rep.warn(w, "race is unverified; confirm against the official candidate list or flag it to the voter")
        if not r.get("key_dynamic"):
            rep.warn(w, "add a key_dynamic (the central dynamic of the race)")
        vote_for = r.get("vote_for") or 1
        cands = r.get("candidates") or []
        if not cands:
            rep.warn(w, "no candidates listed (confirm against the official list; write-ins and vacancies should be noted in key_dynamic)")
        cids = set()
        for ci, c in enumerate(cands):
            cw = f"{w}.candidates[{ci}]({c.get('name', '?')})"
            cid = c.get("id")
            if not cid:
                rep.err(cw, "id required")
            elif cid in cids:
                rep.err(cw, f"duplicate candidate id {cid!r}")
            cids.add(cid)
            if not c.get("name"):
                rep.err(cw, "name required")
            elif re.search(r"[()/&]|\brunning mate\b|\bwith\b", c["name"], re.I):
                rep.warn(cw, "name looks like a ticket or has extra text; keep `name` to the candidate only and put a running mate in `running_mate` (optionally set `short_name` for bar labels)")
            if c.get("record_depth") and c["record_depth"] not in DEPTH:
                rep.err(cw, f"record_depth must be one of {sorted(DEPTH)}")
            if guide_stage and not c.get("record_depth"):
                rep.warn(cw, "set record_depth (deep, moderate, or thin)")
            fit = c.get("fit")
            if guide_stage and len(cands) > 1 and not fit:
                rep.err(cw, "contested race in guide stage needs a fit assessment")
            if fit:
                check_rating(rep, cw + ".fit.overall", fit.get("overall"))
                for bi, b in enumerate(fit.get("by_issue") or []):
                    bw = f"{cw}.fit.by_issue[{bi}]"
                    check_rating(rep, bw + ".rating", b.get("rating"))
                    if b.get("basis") and b["basis"] not in BASIS:
                        rep.err(bw, f"basis must be one of {sorted(BASIS)}")
                    if b.get("rating") in LEGACY_RATINGS:
                        rep.warn(bw, f"legacy rating {b['rating']!r} is treated as {LEGACY_RATINGS[b['rating']]!r}; use the five-level scale")
                    if b.get("rating") in ("strong", "poor", "weak") and not b.get("note"):
                        rep.warn(bw, "strong/weak/poor ratings need an evidence note")
                    if b.get("rating") == "strong" and b.get("basis") == "party_platform":
                        rep.warn(bw, "party-platform evidence is capped at 'good'; scoring will treat 'strong' as 'good'")
                    if b.get("rating") == "strong" and b.get("basis") == "statement":
                        rep.warn(bw, "strong rating rests on statements only; statements cap at 'good' and scoring will treat it as 'good'")
            if guide_stage and len(cands) > 1:
                if not c.get("best_case") or not c.get("strongest_criticism"):
                    rep.warn(cw, "give every candidate both a best case and a strongest criticism (neutrality)")
            for li, l in enumerate(c.get("links") or []):
                check_url(rep, f"{cw}.links[{li}].url", l.get("url"), required=True)
        # neutrality: depth of text symmetric-ish
        if guide_stage and len(cands) > 1:
            lens = [len((c.get("best_case") or "")) + len((c.get("strongest_criticism") or "")) for c in cands]
            if lens and min(lens) > 0 and max(lens) / min(lens) > 3:
                rep.warn(w, "best case / criticism text is very uneven across candidates; check for tone and depth symmetry")
        rec = r.get("recommendation")
        if guide_stage and not rec:
            rep.err(w, "guide stage needs a recommendation block (candidate_ids may be empty with a none_reason)")
        if rec:
            for cid in rec.get("candidate_ids") or []:
                if cid not in cids:
                    rep.err(w, f"recommendation references unknown candidate id {cid!r}")
            if rec.get("confidence") and rec["confidence"] not in CONFIDENCE:
                rep.err(w, f"recommendation.confidence must be one of {sorted(CONFIDENCE)}")
            ids = rec.get("candidate_ids") or []
            if len(ids) > max(vote_for, 1) and not rec.get("tie") and r.get("method", "plurality") == "plurality":
                rep.err(w, f"{len(ids)} best-fit ids but vote_for is {vote_for}; for a tie set recommendation.tie=true")
            if rec.get("tie") and len(ids) < 2:
                rep.err(w, "tie=true needs at least two candidate_ids")
            by_id = {c.get("id"): c for c in cands}
            for cid in ids:
                c = by_id.get(cid) or {}
                f = c.get("fit") or {}
                if f.get("dealbreaker"):
                    rep.err(w, f"recommended candidate {cid!r} has a dealbreaker flag; explain it in caveats or choose another")
                if f.get("overall") in ("poor", "unknown") and ids and len(cands) > 1:
                    rep.warn(w, f"best-fit candidate {cid!r} has overall fit {f.get('overall')!r}; consider 'no clear best fit'")
            if not rec.get("candidate_ids") and not rec.get("none_reason") and guide_stage and len(cands) > 1:
                rep.err(w, "no pick chosen: choose the best available candidate_ids (use tie=true for a toss-up). Use none_reason only when no candidate has any rated issue")
            if rec.get("confidence") in ("low", "medium") and not rec.get("caveats"):
                rep.warn(w, "medium/low confidence should include a caveat")
        check_sources(rep, w, r.get("sources"), required=guide_stage)
        if guide_stage and len(cands) > 1:
            tops = [str(x).lower() for x in ((data.get("profile") or {}).get("top_issues") or [])]
            for c in cands:
                rated = [str(b.get("issue", "")).lower() for b in ((c.get("fit") or {}).get("by_issue") or [])]
                missing = [t for t in tops if t not in rated]
                if missing:
                    rep.warn(f"{w}.candidates({c.get('name', '?')})", f"priority issue(s) not rated (rate them or mark 'na' when the office cannot influence them): {', '.join(missing)}")
                    break

    for mi, m in enumerate(measures):
        w = f"measures[{mi}]({m.get('title', '?')})"
        mid = m.get("id")
        if not mid:
            rep.err(w, "id required")
        elif mid in seen_ids:
            rep.err(w, f"duplicate id {mid!r}")
        seen_ids.add(mid)
        for k in ("level", "title"):
            if not m.get(k):
                rep.err(w, f"{k} required")
        if guide_stage:
            for k in ("yes_means", "no_means"):
                if not m.get(k):
                    rep.err(w, f"{k} required in guide stage (read the official text)")
        for bi, b in enumerate(m.get("by_issue") or []):
            bw = f"{w}.by_issue[{bi}]"
            check_rating(rep, bw + ".yes_rating", b.get("yes_rating"))
            check_rating(rep, bw + ".no_rating", b.get("no_rating"))
        if m.get("status") == "unverified":
            rep.warn(w, "measure is unverified; confirm its status and text")
        if m.get("lean") and m["lean"] not in LEAN:
            rep.err(w, f"lean must be one of {sorted(LEAN)}")
        if m.get("confidence") and m["confidence"] not in CONFIDENCE:
            rep.err(w, f"confidence must be one of {sorted(CONFIDENCE)}")
        if guide_stage and not m.get("lean"):
            rep.err(w, "guide stage needs a lean (use 'undecided' when evidence is mixed)")
        check_sources(rep, w, m.get("sources"), required=guide_stage)

    check_completeness(rep, data)

    if guide_stage and not data.get("profile"):
        rep.warn("profile", "guide stage should include the voter's priorities for transparency")
    for i, s in enumerate(data.get("sources") or []):
        check_url(rep, f"sources[{i}].url", s.get("url"), required=True)

    # Basic safety scan on text content: scripts/markup are rendered as text by the template,
    # but flag anything that looks like markup so it can be cleaned at the source.
    def scan(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                scan(v, f"{path}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                scan(v, f"{path}[{i}]")
        elif isinstance(node, str):
            if re.search(r"<\s*(script|iframe|object|embed)\b", node, re.I):
                rep.warn(path, "contains script-like markup; it will be shown as plain text, but check where it came from")
    scan(data, "data")

    def check_placeholders(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                check_placeholders(v, f"{path}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                check_placeholders(v, f"{path}[{i}]")
        elif isinstance(node, str) and re.search(r"https?://(www\.)?example\.(org|com)\b", node):
            rep.warn(path, "example.org/example.com URL; replace with a real source before delivering")
    if not meta.get("is_sample"):
        check_placeholders(data, "data")
    else:
        rep.warn("meta.is_sample", "is_sample is true; remove it from a real guide")
    return rep


# ---------------------------------------------------------------------------
# Scoring: a transparent 0-100 alignment score, evidence coverage, and a decision label.
# Inputs are only the qualitative ratings and the voter's priority order, so the numbers can be
# reproduced by hand. The score measures alignment with the voter's stated priorities where
# evidence exists; coverage says how much of what matters was actually evidenced.
# ---------------------------------------------------------------------------
POINTS = {"strong": 1.0, "good": 0.75, "mixed": 0.5, "weak": 0.25, "poor": 0.0}
UNKNOWN_LOW, UNKNOWN_HIGH = 0.25, 0.75   # unrated issues are assumed to land between Weak and Good


def issue_weights(profile):
    """Weight per issue: biggest priorities 5,4,3,3,... by rank; all other issues 1."""
    w = {}
    for i, name in enumerate((profile or {}).get("top_issues") or []):
        w[str(name).strip().lower()] = max(3, 5 - i)
    for name in (profile or {}).get("other_issues") or []:
        w.setdefault(str(name).strip().lower(), 1)
    return w


def norm_rating(r):
    return LEGACY_RATINGS.get(r, r)


def points_for(rating, basis):
    """Points for a rating after evidence caps: statements and party platforms cap at 'good'."""
    pts = POINTS.get(norm_rating(rating), 0.0)
    if basis in ("statement", "party_platform"):
        pts = min(pts, POINTS["good"])
    return pts


def aggregate(entries, weights):
    """entries: iterable of (issue, rating, basis). Returns (score, low, high, coverage) or Nones."""
    num = den = unk = full_rated = full_all = 0.0
    for issue, rating, basis in entries:
        rating = norm_rating(rating)
        if rating in (None, "na"):
            continue
        w = weights.get(str(issue or "").strip().lower(), 1)
        full_all += w
        if rating == "unknown":
            unk += w
            continue
        mult = 0.5 if basis == "party_platform" else 1.0
        num += w * mult * points_for(rating, basis)
        den += w * mult
        full_rated += w * mult
    if not (den or unk):
        return None, None, None, None
    score = round(100 * num / den) if den else None
    total = den + unk
    low = round(100 * (num + UNKNOWN_LOW * unk) / total)
    high = round(100 * (num + UNKNOWN_HIGH * unk) / total)
    coverage = round(100 * full_rated / full_all) if full_all else None
    return score, low, high, coverage


def score_candidate(cand, weights):
    return aggregate([(b.get("issue"), b.get("rating"), b.get("basis")) for b in (cand.get("fit") or {}).get("by_issue") or []], weights)


def decide(top_score, second_score, cov, robust):
    margin = None if second_score is None else top_score - second_score
    if margin is None:
        return None, "slight"
    d = "clear" if margin >= 15 else "lean" if margin >= 8 else "slight" if margin >= 3 else "toss_up"
    if d == "clear" and not robust:
        d = "lean"
    if cov < 60 and d == "clear":
        d = "lean"
    if cov < 40 and d in ("clear", "lean"):
        d = "slight"
    return margin, d


def apply_scoring(data, rep):
    weights = issue_weights(data.get("profile"))
    for m in data.get("measures") or []:
        if not (m.get("by_issue") or []):
            continue
        ye = [(b.get("issue"), b.get("yes_rating"), None) for b in m["by_issue"]]
        ne = [(b.get("issue"), b.get("no_rating"), None) for b in m["by_issue"]]
        ys, ylo, yhi, yc = aggregate(ye, weights)
        ns, nlo, nhi, nc = aggregate(ne, weights)
        m["yes_score"], m["no_score"] = ys, ns
        m["yes_range"], m["no_range"] = [ylo, yhi], [nlo, nhi]
        covs = [c for c in (yc, nc) if c is not None]
        m["coverage"] = min(covs) if covs else None
        if ys is None or ns is None:
            continue
        gap = ys - ns
        hi_side, lo_side = ("yes", "no") if gap >= 0 else ("no", "yes")
        robust = m[hi_side + "_range"][0] > m[lo_side + "_range"][1]
        margin, strength = decide(max(ys, ns), min(ys, ns), m["coverage"] or 0, robust)
        m["margin"], m["decision"], m["robust"] = abs(gap), strength, robust
        m["suggested_lean"] = "undecided" if strength == "toss_up" else hi_side
        if m.get("lean") and m["lean"] != m["suggested_lean"] and strength in ("clear", "lean"):
            rep.warn(f"measures({m.get('title', '?')})", f"lean {m['lean']!r} disagrees with the scores (YES {ys}, NO {ns}); fix the ratings or explain")
    for r in data.get("races") or []:
        cands = r.get("candidates") or []
        for c in cands:
            if c.get("fit"):
                sc, lo, hi, cov = score_candidate(c, weights)
                c["fit"]["score"], c["fit"]["score_low"], c["fit"]["score_high"], c["fit"]["coverage"] = sc, lo, hi, cov
        if len(cands) < 2 or (r.get("vote_for") or 1) > 1 or r.get("recommendation") is None:
            continue
        rec = r["recommendation"]
        pool = [c for c in cands if (c.get("fit") or {}).get("score") is not None and not (c.get("fit") or {}).get("dealbreaker")]
        if not pool:
            continue
        pool.sort(key=lambda c: -c["fit"]["score"])
        top = pool[0]
        if len(pool) == 1:
            margin, decision, robust, cov = None, "slight", False, top["fit"].get("coverage") or 0
        else:
            sec = pool[1]
            robust = top["fit"]["score_low"] > sec["fit"]["score_high"]
            cov = min(top["fit"].get("coverage") or 0, sec["fit"].get("coverage") or 0)
            margin, decision = decide(top["fit"]["score"], sec["fit"]["score"], cov, robust)
        level = {"clear": 4, "lean": 3, "slight": 2, "toss_up": 1}[decision]
        if cov >= 80 and top.get("record_depth") == "deep":
            level += 1
        if cov < 40:
            level -= 1
        level = max(1, min(5, level))
        rec["decision"], rec["margin"], rec["top_score"], rec["robust"] = decision, margin, top["fit"]["score"], robust
        rec["suggested_confidence"] = CONF_ORDER[level - 1]
        if not rec.get("confidence"):
            rec["confidence"] = rec["suggested_confidence"]
        elif rec["confidence"] in CONF_ORDER and abs(CONF_ORDER.index(rec["confidence"]) - (level - 1)) > 1:
            rep.warn(f"races({r.get('office', '?')})", f"confidence {rec['confidence']!r} is far from the evidence-based {rec['suggested_confidence']!r}; justify in caveats or adjust")
        ids = rec.get("candidate_ids") or []
        if decision == "toss_up" and not rec.get("tie") and len(pool) > 1:
            rep.warn(f"races({r.get('office', '?')})", "scores are within 3 points; set recommendation.tie=true and list both candidates, or explain the tiebreaker in reasoning")
        if ids and not rec.get("tie") and ids[0] != top.get("id") and decision != "toss_up":
            rep.warn(f"races({r.get('office', '?')})", f"best-fit pick {ids[0]!r} differs from the top alignment score ({top.get('id')!r}); explain why in reasoning or fix the ratings")


def build(data, out_path):
    template = TEMPLATE.read_text(encoding="utf-8")
    if "__GUIDE_DATA__" not in template or "__TITLE__" not in template:
        raise SystemExit("template placeholders missing")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    payload = (payload.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
               .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))
    title = escape(str(data["meta"].get("title", "Voter Guide")), quote=True)
    html = template.replace("__TITLE__", title).replace("__GUIDE_DATA__", payload)
    Path(out_path).write_text(html, encoding="utf-8")
    return len(html)


def main(argv):
    args = argv[1:]
    check_only = "--check" in args
    sample = "--sample" in args
    args = [a for a in args if a not in ("--check", "--sample")]
    try:
        if sample:
            data_path = SAMPLE
            out = args[0] if args else None
        else:
            if not args:
                print(__doc__)
                return 2
            data_path = Path(args[0])
            out = args[1] if len(args) > 1 else None
        data = json.loads(Path(data_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"Cannot read data: {e}", file=sys.stderr)
        return 2

    rep = validate(data)
    if not rep.errors:
        apply_scoring(data, rep)
    if out and Path(out).resolve() == TEMPLATE.resolve():
        print("Refusing to overwrite the template; give an output path outside assets/.", file=sys.stderr)
        return 2
    for line in rep.errors + rep.warnings:
        print(line)
    print(f"{len(rep.errors)} error(s), {len(rep.warnings)} warning(s)")
    if rep.errors:
        return 1
    if check_only:
        return 0
    if not out:
        print("No output path given; nothing built.", file=sys.stderr)
        return 2
    size = build(data, out)
    print(f"Built {out} ({size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
