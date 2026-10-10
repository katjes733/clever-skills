# Contributing

- One skill per folder under `skills/`; the folder name must equal the `name` in its `SKILL.md`.
- Keep each skill self-contained: everything it ships must use paths relative to its own folder. Development files (tests, docs, examples, README, CHANGELOG) stay at the top level of the skill folder so the packager can leave them out.
- Run `make check` before pushing; CI runs it and packages every skill.
- Skill-specific rules live in that skill's own `CONTRIBUTING.md`.
- Never commit personal data produced by a skill (see `.gitignore`).
