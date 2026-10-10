#!/usr/bin/env python3
"""Package a skill from skills/<name>/ into dist/<name>.skill (a zip with the skill folder at its root).

Usage:
  python3 tools/package_skill.py <name> [OUTPUT_DIR]
  python3 tools/package_skill.py --all [OUTPUT_DIR]

Only the files Claude needs are shipped. Development files at the top level of the skill folder
(README, CHANGELOG, CONTRIBUTING, LICENSE, Makefile, tests/, docs/, examples/) are left out.
A skill may override this with a `.skillignore` file (one top-level name per line).
"""
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
TOP_LEVEL_EXCLUDE = {"README.md", "CHANGELOG.md", "CONTRIBUTING.md", "LICENSE", "Makefile",
                     "tests", "docs", "examples", "dist", ".skillignore"}
ANY_LEVEL_EXCLUDE = {"__pycache__", ".git", ".DS_Store"}


def frontmatter(skill_md):
    m = re.match(r"---\n(.*?)\n---\n", skill_md.read_text(encoding="utf-8"), re.S)
    if not m:
        raise ValueError("SKILL.md has no frontmatter")
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip("\"'")
    return fm


def validate(skill):
    md = skill / "SKILL.md"
    if not md.is_file():
        raise ValueError(f"{skill}: SKILL.md not found")
    fm = frontmatter(md)
    if fm.get("name") != skill.name:
        raise ValueError(f"{skill.name}: frontmatter name {fm.get('name')!r} must equal the folder name")
    desc = fm.get("description", "")
    if not desc or len(desc) > 1024 or "<" in desc:
        raise ValueError(f"{skill.name}: description must be 1-1024 chars with no '<'")


def package(skill, out_dir):
    validate(skill)
    exclude = set(TOP_LEVEL_EXCLUDE)
    ignore = skill / ".skillignore"
    if ignore.is_file():
        exclude = {l.strip() for l in ignore.read_text().splitlines() if l.strip() and not l.startswith("#")} | {".skillignore"}
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{skill.name}.skill"
    n = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(skill.rglob("*")):
            rel = p.relative_to(skill)
            if p.is_dir() or rel.parts[0] in exclude or any(x in ANY_LEVEL_EXCLUDE for x in rel.parts) or p.suffix == ".pyc":
                continue
            z.write(p, Path(skill.name) / rel)
            n += 1
    print(f"Wrote {out} ({n} files)")


def main(argv):
    args = argv[1:]
    if not args:
        print(__doc__, file=sys.stderr)
        return 2
    out_dir = Path(args[1]) if len(args) > 1 else ROOT / "dist"
    try:
        if args[0] == "--all":
            for s in sorted(p for p in SKILLS.iterdir() if (p / "SKILL.md").is_file()):
                package(s, out_dir)
        else:
            package(SKILLS / args[0], out_dir)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
