"""Tests for the guide builder: validation, scoring, template safety, and skill metadata.

Run from the repository root:  make test SKILL=election-voter-guide
No third-party dependencies.
"""
import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path

DEV_DIR = Path(__file__).resolve().parent.parent     # dev/<name>/ (this folder's parent)
ROOT = DEV_DIR.parent.parent
SKILL = ROOT / "skills" / DEV_DIR.name               # skills/<name>/, the shipped skill
SCRIPT = SKILL / "scripts" / "build_guide.py"

spec = importlib.util.spec_from_file_location("build_guide", SCRIPT)
bg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bg)


def load_sample():
    return json.loads((SKILL / "assets" / "sample-guide.json").read_text(encoding="utf-8"))


class SampleTests(unittest.TestCase):
    def test_sample_validates_without_errors(self):
        rep = bg.validate(load_sample())
        self.assertEqual(rep.errors, [])

    def test_sample_builds_and_embeds_data(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "guide.html"
            self.assertEqual(bg.main(["build_guide.py", str(SKILL / "assets" / "sample-guide.json"), str(out)]), 0)
            html = out.read_text(encoding="utf-8")
            self.assertIn('id="guide-data"', html)
            self.assertNotIn("__GUIDE_DATA__", html)

    def test_refuses_to_overwrite_template(self):
        tpl = SKILL / "assets" / "voter-guide-template.html"
        before = tpl.read_text(encoding="utf-8")
        code = bg.main(["build_guide.py", str(SKILL / "assets" / "sample-guide.json"), str(tpl)])
        self.assertEqual(code, 2)
        self.assertEqual(tpl.read_text(encoding="utf-8"), before)

    def test_embedded_json_cannot_close_the_script_tag(self):
        data = load_sample()
        data["meta"]["title"] = "T"
        data["races"][0]["key_dynamic"] = "</script><script>alert(1)</script> & <b>"
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "g.html"
            bg.build(data, out)
            html = out.read_text(encoding="utf-8")
        template = (SKILL / "assets" / "voter-guide-template.html").read_text(encoding="utf-8")
        self.assertEqual(html.count("</script>"), template.count("</script>"))
        self.assertNotIn("<script>alert(1)", html)


class ScoringTests(unittest.TestCase):
    def test_weights_by_rank(self):
        w = bg.issue_weights({"top_issues": ["A", "B", "C", "D"], "other_issues": ["E"]})
        self.assertEqual([w["a"], w["b"], w["c"], w["d"], w["e"]], [5, 4, 3, 3, 1])

    def test_weighted_score(self):
        w = {"a": 5, "b": 4}
        score, low, high, cov = bg.aggregate([("A", "strong", "record"), ("B", "mixed", "record")], w)
        self.assertEqual((score, low, high, cov), (78, 78, 78, 100))

    def test_statements_cap_at_good(self):
        score, *_ = bg.aggregate([("A", "strong", "statement")], {"a": 5})
        self.assertEqual(score, 75)

    def test_party_platform_is_half_weight_and_capped(self):
        score, _, _, cov = bg.aggregate([("A", "strong", "party_platform")], {"a": 5})
        self.assertEqual(score, 75)
        self.assertEqual(cov, 50)

    def test_unknown_widens_range_and_lowers_coverage(self):
        score, low, high, cov = bg.aggregate([("A", "strong", "record"), ("B", "unknown", None)], {"a": 5, "b": 4})
        self.assertEqual((score, low, high, cov), (100, 67, 89, 56))

    def test_not_applicable_is_ignored(self):
        score, low, high, cov = bg.aggregate([("A", "good", "record"), ("B", "na", None)], {"a": 3, "b": 3})
        self.assertEqual((score, low, high, cov), (75, 75, 75, 100))

    def test_all_unknown_has_no_score(self):
        score, low, high, cov = bg.aggregate([("A", "unknown", None)], {"a": 5})
        self.assertIsNone(score)
        self.assertEqual(cov, 0)

    def test_legacy_moderate_is_mixed(self):
        score, *_ = bg.aggregate([("A", "moderate", "record")], {"a": 5})
        self.assertEqual(score, 50)

    def test_decision_labels(self):
        self.assertEqual(bg.decide(90, 60, 80, True)[1], "clear")
        self.assertEqual(bg.decide(90, 60, 80, False)[1], "lean")   # ranges overlap
        self.assertEqual(bg.decide(90, 60, 50, True)[1], "lean")    # thin coverage
        self.assertEqual(bg.decide(90, 60, 30, True)[1], "slight")  # very thin coverage
        self.assertEqual(bg.decide(80, 70, 90, True)[1], "lean")
        self.assertEqual(bg.decide(75, 70, 90, True)[1], "slight")
        self.assertEqual(bg.decide(75, 74, 90, True)[1], "toss_up")

    def test_sample_scoring_is_applied_to_races_and_measures(self):
        data = load_sample()
        rep = bg.validate(data)
        bg.apply_scoring(data, rep)
        house = next(r for r in data["races"] if r["id"] == "r-house")
        self.assertIn(house["recommendation"]["decision"], bg.DECISIONS)
        for c in house["candidates"]:
            self.assertIsNotNone(c["fit"]["score"])
            self.assertLessEqual(c["fit"]["score_low"], c["fit"]["score_high"])
        measure = next(m for m in data["measures"] if m["id"] == "m-1")
        self.assertIsNotNone(measure["yes_score"])
        self.assertEqual(measure["suggested_lean"], "yes")


class ValidationTests(unittest.TestCase):
    def test_bad_rating_is_an_error(self):
        data = load_sample()
        data["races"][0]["candidates"][0]["fit"]["by_issue"][0]["rating"] = "great"
        self.assertTrue(any("rating" in e for e in bg.validate(data).errors))

    def test_duplicate_candidate_ids_are_an_error(self):
        data = load_sample()
        cands = data["races"][0]["candidates"]
        cands[1]["id"] = cands[0]["id"]
        self.assertTrue(any("duplicate" in e for e in bg.validate(data).errors))

    def test_non_http_urls_are_rejected(self):
        data = load_sample()
        data["sources"][0]["url"] = "javascript:alert(1)"
        self.assertTrue(bg.validate(data).errors)


class CompletenessTests(unittest.TestCase):
    def errors(self, data):
        return bg.validate(data).errors

    def test_sample_inventory_matches_guide(self):
        data = load_sample()
        self.assertEqual(self.errors(data), [])
        exp = {e["id"] for e in data["completeness"]["expected"]}
        ids = {r["id"] for r in data["races"]} | {m["id"] for m in data["measures"]}
        self.assertEqual(exp, ids)

    def test_missing_completeness_block_is_an_error(self):
        data = load_sample()
        del data["completeness"]
        self.assertTrue(any("completeness" in e for e in self.errors(data)))

    def test_inventory_item_missing_from_guide_is_an_error(self):
        data = load_sample()
        data["races"] = [r for r in data["races"] if r["id"] != "r-sheriff"]
        errs = self.errors(data)
        self.assertTrue(any("r-sheriff" in e and "not in the guide" in e for e in errs))

    def test_guide_item_missing_from_inventory_warns(self):
        data = load_sample()
        data["completeness"]["expected"] = [e for e in data["completeness"]["expected"] if e["id"] != "r-assessor"]
        warnings = bg.validate(data).warnings
        self.assertTrue(any("r-assessor" in w and "not in the inventory" in w for w in warnings))

    def test_measure_type_is_checked_against_measures(self):
        data = load_sample()
        for e in data["completeness"]["expected"]:
            if e["id"] == "m-1":
                e["type"] = "race"
        self.assertTrue(any("m-1" in e for e in self.errors(data)))

    def test_guide_stage_requires_independent_check(self):
        data = load_sample()
        data["meta"]["stage"] = "guide"
        data["completeness"]["independent_check"] = {"done": False}
        self.assertTrue(any("independent_check" in e for e in self.errors(data)))
        data["completeness"]["independent_check"] = {"done": False, "skipped_reason": "no subagents available"}
        self.assertFalse(any("independent_check" in e for e in self.errors(data)))

    def test_profile_stage_only_warns_without_independent_check(self):
        data = load_sample()
        data["meta"]["stage"] = "profile"
        data["completeness"].pop("independent_check")
        rep = bg.validate(data)
        self.assertFalse(any("independent_check" in e for e in rep.errors))
        self.assertTrue(any("independent_check" in w for w in rep.warnings))

    def test_warns_when_no_official_list_among_sources(self):
        data = load_sample()
        for s in data["completeness"]["sources"]:
            s["kind"] = "aggregator"
        self.assertTrue(any("needs no street address" in w for w in bg.validate(data).warnings))

    def test_unresolved_items_are_reported(self):
        warnings = bg.validate(load_sample()).warnings
        self.assertTrue(any("not confirmed" in w for w in warnings))

    def test_bad_source_kind_and_url(self):
        data = load_sample()
        data["completeness"]["sources"][0]["kind"] = "rumor"
        data["completeness"]["sources"][1]["url"] = "javascript:alert(1)"
        errs = self.errors(data)
        self.assertTrue(any("kind" in e for e in errs))
        self.assertTrue(any("url" in e for e in errs))


class TicketTests(unittest.TestCase):
    def test_sample_has_ticket_race_without_name_warning(self):
        data = load_sample()
        gov = next(r for r in data["races"] if r["id"] == "r-gov")
        self.assertTrue(all(c.get("running_mate") for c in gov["candidates"]))
        warnings = bg.validate(data).warnings
        self.assertFalse([w for w in warnings if "looks like a ticket" in w])

    def test_ticket_style_name_warns(self):
        data = load_sample()
        gov = next(r for r in data["races"] if r["id"] == "r-gov")
        gov["candidates"][0]["name"] = "Morgan Placeholder (running mate: Riley Fictional)"
        warnings = bg.validate(data).warnings
        self.assertTrue([w for w in warnings if "looks like a ticket" in w])


class SkillMetadataTests(unittest.TestCase):
    def test_frontmatter(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        self.assertIsNotNone(m, "SKILL.md needs YAML frontmatter")
        front = m.group(1)
        name = re.search(r"^name:\s*(.+)$", front, re.M).group(1).strip().strip("\"'")
        desc = re.search(r"^description:\s*(.+)$", front, re.M).group(1).strip()
        self.assertEqual(name, SKILL.name)
        self.assertLessEqual(len(desc), 1024)
        self.assertNotIn("<", desc)

    def test_referenced_files_exist(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for rel in set(re.findall(r"`((?:references|assets|scripts)/[A-Za-z0-9_./-]+)`", text)):
            if "*" in rel:
                continue
            self.assertTrue((SKILL / rel).exists(), f"SKILL.md references missing file {rel}")

    def test_no_stale_top_three_language(self):
        shipped = [SKILL / "SKILL.md"] + list((SKILL / "references").rglob("*.md"))   # shipped files only
        for p in shipped + [SKILL / "assets" / "voter-guide-template.html"]:
            if "snapshots" in p.parts:
                continue
            self.assertNotRegex(p.read_text(encoding="utf-8"), r"(?i)top three")


if __name__ == "__main__":
    unittest.main()
