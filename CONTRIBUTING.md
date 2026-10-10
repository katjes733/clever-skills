# Contributing

- One skill per folder under `skills/`; the folder name must equal the `name` in its `SKILL.md`.
- `skills/<name>/` holds only what an agent needs (`SKILL.md`, `references/`, `assets/`, `scripts/`). Installers copy the whole folder, so tests, docs, examples, the README, the CHANGELOG and the skill's own contributing rules live in `dev/<name>/`.
- Keep each skill self-contained: everything it ships must use paths relative to its own folder.
- Run `bun run verify` before pushing; CI runs the same checks and packages every skill.
- Releases use [Changesets](https://github.com/changesets/changesets). For any change users would notice, run `bun run changeset`, pick a bump (patch, minor, major) and describe it. Merging to `main` opens a "chore: version skills" PR; merging that bumps the version in `package.json` and `.claude-plugin/plugin.json`, writes `CHANGELOG.md` and tags `v<version>`. Claude Code only offers an update when that version changes.
- Skill-specific rules live in `dev/<name>/CONTRIBUTING.md`.
- Never commit personal data produced by a skill (see `.gitignore`).
