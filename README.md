# Skills

A personal collection of [agent skills](https://agentskills.io), each developed, tested and packaged from one repository.

| Skill | What it does |
|---|---|
| [`election-voter-guide`](skills/election-voter-guide) ([docs](dev/election-voter-guide/README.md)) | Interviews you about your priorities and positions, researches your actual ballot, and builds an interactive, evidence-based voter guide. |

## Installation

Pick **one** route per agent. Installing through two routes gives you every skill twice.

### Claude Code

```bash
claude plugin marketplace add katjes733/clever-skills
claude plugin install clever-skills@clever-skills
```

Update with:

```bash
claude plugin marketplace update clever-skills
claude plugin update clever-skills@clever-skills
```

You can also turn on auto-update for the `clever-skills` marketplace in `/plugin`. Releases reach installed users when the plugin `version` changes, so see [Releasing](#releasing).

### Any other agent, or editable files (manual updates)

```bash
npx skills@latest add katjes733/clever-skills -a <agent>   # claude-code, codex, cursor, opencode, ...; omit -a to choose
npx skills@latest add katjes733/clever-skills --skill election-voter-guide   # just one skill
```

The [skills CLI](https://github.com/vercel-labs/skills) supports about 75 agents. To update, run `npx skills@latest update`, and re-run `add` to pick up new skills.

### From a clone (for development, updates with `git pull`)

```bash
git clone https://github.com/katjes733/clever-skills && cd clever-skills
bun install
make install        # symlinks every skill into ~/.claude/skills and ~/.agents/skills
make uninstall      # removes those links again
```

Options go in `ARGS`, for example `make install ARGS="--dest ~/my-agent/skills --skill election-voter-guide --copy --dry-run"`. A real directory with the same name is never replaced unless you pass `--force`.

### Claude app (upload)

`make package SKILL=<name>` writes `dist/<name>.skill`; upload it in Claude's skills settings. Remove an older copy first, since a new upload may not replace an installed one.

## Layout

```
skills/<name>/             What agents install. Folder name == `name` in SKILL.md frontmatter.
  SKILL.md  references/  assets/  scripts/
dev/<name>/                Development files for that skill, never installed.
  README.md  CHANGELOG.md  CONTRIBUTING.md  tests/  docs/  examples/  Makefile
.claude-plugin/            plugin.json (generated from skills/ and package.json) and marketplace.json
scripts/                   install.mjs (make install), sync-plugin.mjs, and their tests
tools/package_skill.py     Builds dist/<name>.skill
.changeset/                Pending release notes
.github/workflows/         ci.yml (verify and package) and release.yml (version PR and tags)
```

## Common tasks

```bash
bun run verify                            # everything CI checks
make test SKILL=election-voter-guide      # one skill's tests
make check                                # tests + sample build for every skill
make package-all                          # dist/*.skill
bun run changeset                         # describe a change for the next release
```

## Adding a skill

1. Create `skills/<name>/SKILL.md` (frontmatter `name` must equal `<name>`; description under 1024 characters, no `<`). Put only what the agent needs in that folder.
2. Add a row to the table above. `bun run sync` rewrites `.claude-plugin/plugin.json` to list the new skill, and `bun run verify` fails if you forget either step.
3. Optional: add `dev/<name>/` with tests, docs and a `Makefile` that defines `check`. CI runs `check` for every skill that has one.
4. Run `bun run changeset` (minor for a new skill). That is all the release needs.

The `skills` CLI route and `make install` discover the new folder on their own.

## Releasing

Merging to `main` makes the Release workflow open a "chore: version skills" PR that collects the pending changesets. Merging it bumps `package.json` and `.claude-plugin/plugin.json`, updates `CHANGELOG.md` and tags `v<version>`. The repository needs *Settings, Actions, General, Allow GitHub Actions to create and approve pull requests* enabled. Run `claude plugin validate . --strict` after editing either manifest by hand.

## License

MIT, see [LICENSE](LICENSE).
