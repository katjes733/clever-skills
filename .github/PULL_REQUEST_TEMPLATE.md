**ISSUE:** #

**SKILL(S):** Folder name(s) under `skills/`, or "tooling".

**DESCRIPTION:** A clear and concise description of the changes you have made.

**TESTING:** Describe the testing you have performed. For behavior changes, include an example
prompt and what the agent did.

**CONTEXT:** Add any other context about your contribution here.

**CHECKLIST:**

- [ ] `SKILL.md` name matches folder; `description` still says what the skill does and when to use it
- [ ] Skill is self-contained (relative paths); tests, docs and examples live in `dev/<name>/`, not in the skill
- [ ] Tests added/updated as needed
- [ ] `bun run verify` passes
- [ ] Changeset added with `bun run changeset` (skip for dev-only changes)
