// Shared helpers: find the skills under skills/ and read their SKILL.md frontmatter.

import { existsSync, readdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

export const REPO = join(dirname(fileURLToPath(import.meta.url)), "..", "..");

/** Read the top-level `key: value` pairs of a SKILL.md frontmatter block. */
export function parseFrontmatter(markdown) {
  const match = markdown.match(/^---\n([\s\S]*?)\n---\n/);
  if (!match) throw new Error("SKILL.md has no frontmatter");
  const fields = {};
  for (const line of match[1].split("\n")) {
    const pair = line.match(/^([A-Za-z0-9_-]+):\s*(.*)$/);
    if (pair) fields[pair[1]] = pair[2].trim().replace(/^["']|["']$/g, "");
  }
  return fields;
}

/**
 * List every skill under `<repo>/skills/<name>/SKILL.md`, sorted by name.
 * Throws if a folder name differs from the frontmatter `name`, because every installer keys on it.
 */
export function listSkills(repo = REPO) {
  const root = join(repo, "skills");
  if (!existsSync(root)) return [];
  return readdirSync(root, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && existsSync(join(root, entry.name, "SKILL.md")))
    .map((entry) => {
      const dir = join(root, entry.name);
      const { name, description } = parseFrontmatter(readFileSync(join(dir, "SKILL.md"), "utf8"));
      if (name !== entry.name) {
        throw new Error(`skills/${entry.name}: frontmatter name ${JSON.stringify(name)} must equal the folder name`);
      }
      return { name, description, dir };
    })
    .sort((a, b) => a.name.localeCompare(b.name));
}
