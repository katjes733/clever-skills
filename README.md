# Skills

A personal collection of [Claude skills](https://support.claude.com/en/articles/12512180-using-skills-in-claude), each developed, tested and packaged from one repository.

| Skill | What it does |
|---|---|
| [`election-voter-guide`](skills/election-voter-guide) | Interviews you about your priorities and positions, researches your actual ballot, and builds an interactive, evidence-based voter guide. |

## Layout

```
skills/
  <skill-name>/            Folder name == `name` in SKILL.md frontmatter
    SKILL.md               \
    references/             |  shipped in the .skill
    assets/                 |
    scripts/               /
    README.md  CHANGELOG.md  CONTRIBUTING.md   development files, not shipped
    tests/  docs/  examples/  Makefile         development files, not shipped
tools/package_skill.py     Builds dist/<skill-name>.skill
.github/workflows/ci.yml   Tests and packages every skill under skills/
```

## Common tasks

```bash
make test SKILL=election-voter-guide      # one skill's tests
make check                                # tests + sample build for every skill
make package SKILL=election-voter-guide   # dist/election-voter-guide.skill
make package-all
```

## Adding a skill

1. Create `skills/<name>/SKILL.md` (frontmatter `name` must equal `<name>`; description under 1024 characters, no `<`).
2. Optional: add `tests/`, a `Makefile` with a `check` target, a README and a CHANGELOG. CI picks up any skill automatically, and runs `check` for those that define a Makefile.
3. `make package SKILL=<name>`. The packager validates the frontmatter and leaves out development files (override with a `.skillignore` listing top-level names to omit).

## Installing a skill

Upload `dist/<name>.skill` in Claude's skills settings (remove an older copy first; a new upload may not replace an installed one). For Claude Code, copy or symlink `skills/<name>` into `~/.claude/skills/` or a project's `.claude/skills/`.

## License

MIT, see [LICENSE](LICENSE).
