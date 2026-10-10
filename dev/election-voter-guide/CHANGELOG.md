# Changelog

History up to 0.5.0. From now on, releases are tracked by Changesets in the repository root `CHANGELOG.md`.

## Unreleased

- Repository moved to a multi-skill layout (`skills/election-voter-guide/`). No change to the shipped skill; the packager now leaves development files out of the `.skill`.

## 0.5.0 (2026-10-10)
- **Completeness gate.** The ballot inventory is built first from address-free official sources (county candidate list, county sample ballots per ballot style, state lists, voter pamphlet) and recorded in a required `completeness` block. `build_guide.py` errors if an inventory item is missing from the guide, warns about guide items missing from the inventory and about unresolved seats, and (at the guide stage) requires an independent blind re-check or a stated reason it was skipped.
- **Independent blind inventory.** A separate verifier builds its own office and measure list from the same sources without seeing the guide; differences are reconciled and recorded. The claim spot-check no longer stands in for completeness.
- **Address-free sources first.** The street-address warning applies only to the district lookup; it no longer steers research away from the county candidate PDF.
- **Honest reporting.** The voter is no longer asked "does this look complete?"; the skill reports what it checked and what it could not confirm. The Ballot tab shows a "How this list was checked" card and the cheat sheet notes sources and unresolved items.

## 0.4.2 (2026-10-09)
- Audit of every place a candidate name is rendered. New name helpers in the page: `displayName` (card heading), `ticketName` (candidate plus "(with running mate)" for the ballot list, recommendation headline, pick controls, rank selectors, and cheat sheet), and `surname` (bars). The running mate's surname can no longer be used as a label for a ticket.
- Search also matches running mates.

## 0.4.1 (2026-10-09)
- Fix: bar labels for ticket races (governor and lieutenant governor) showed the running mate's surname. Labels now use the top-of-ticket candidate, `running_mate` is a separate field shown on the card, `short_name` overrides the label, and the validator warns about ticket-style names.
- Mobile: in the side-by-side chart the name and rating share a row with the bar full width beneath; compact ratings drop the redundant glyph bar.
- Sample data now includes a governor ticket.

## 0.4.0 (2026-10-08)
- Five-level per-issue ratings (Strong, Good, Mixed, Weak, Poor fit) plus Not enough info / Not applicable.
- Alignment score now carries a likely range (unrated issues assumed between Weak and Good); "Clear best fit" requires non-overlapping ranges.
- Horizontal bars: per-issue bars on each candidate card, a side-by-side chart per race, YES/NO fit bars for measures.
- Build script refuses to overwrite the template.

## 0.3.0 (2026-10-08)
- Alignment score (0 to 100), evidence coverage, decision labels, five-level confidence, computed by `build_guide.py`.
- Always give the best available pick; "no pick" only when nothing could be rated.
- Party-platform evidence allowed at half weight, capped, labeled.
- Research budget and "dig before you give up" guidance to cut web-search approvals and unknown ratings.

## 0.2.0 (2026-10-08)
- Issue menu expanded to about 50 topics, walked in themed tap rounds with no cap.
- Priorities sorted into ranked biggest priorities and also-important issues; stance question for every priority.
- Interview script embedded in `SKILL.md` so it wins over any outdated reference file.

## 0.1.1 (2026-10-08)
- Interview-first rewrite: prime directive, no research or artifact until the core interview is done, tap-to-answer default.

## 0.1.0 (2026-10-08)
- Initial skill: workflow, playbooks, 2026 U.S. midterm snapshot, data-driven guide page, build script.
