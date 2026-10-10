# Contributing

- Run `make test SKILL=election-voter-guide` from the repository root (or `bun run verify` for everything) before sending changes. CI runs the same tests, builds the sample, and packages the skill.
- **Neutrality is a feature.** Interview options and issue names must be worded neutrally and symmetrically; ratings must come from evidence; never display the best-fit candidate first. Changes that tilt the output toward a viewpoint will not be accepted.
- **Never color alone.** Any new rating or visual encoding needs a text label and a non-color cue.
- **No real voter data** in the repository (no addresses, preferences, or real guides). Use the fictional sample.
- Election facts belong in `references/snapshots/`, dated, with sources. Do not hard-code them into `SKILL.md` or the template.
- Keep `SKILL.md` under about 500 lines and its description under 1024 characters; move detail into `references/`.
- If you change the data format, update `scripts/build_guide.py`, the template, `assets/sample-guide.json`, `references/presentation-guide.md`, and the tests together.
