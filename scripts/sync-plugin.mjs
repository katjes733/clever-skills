#!/usr/bin/env node
// Keeps .claude-plugin/plugin.json in step with the repo: the `skills` array lists every folder under
// skills/, and `version` copies package.json's. Runs after `changeset version` in `bun run version`.
// With --check it changes nothing and exits 1 on drift. Also checks every skill is linked in README.md.
//
//   node scripts/sync-plugin.mjs [--check] [--repo <dir>]

import { readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { REPO, listSkills } from "./lib/skills.mjs";

/** Compute the plugin manifest the repo should have, from package.json and the skills folder. */
export function expectedPlugin(current, pkg, skills) {
  return { ...current, version: pkg.version, skills: skills.map((skill) => `./skills/${skill.name}`) };
}

/** Skills whose folder is not linked from the README skill table. */
export function missingFromReadme(readme, skills) {
  return skills.filter((skill) => !readme.includes(`skills/${skill.name}`)).map((skill) => skill.name);
}

export function run(argv, repo = REPO) {
  const check = argv.includes("--check");
  const pluginPath = join(repo, ".claude-plugin", "plugin.json");
  const pkg = JSON.parse(readFileSync(join(repo, "package.json"), "utf8"));
  const current = JSON.parse(readFileSync(pluginPath, "utf8"));
  const skills = listSkills(repo);
  const wanted = JSON.stringify(expectedPlugin(current, pkg, skills), null, 2) + "\n";
  const problems = [];

  if (readFileSync(pluginPath, "utf8") !== wanted) {
    if (check) problems.push("plugin.json is out of date. Run `bun run sync`.");
    else {
      writeFileSync(pluginPath, wanted);
      console.log(`plugin.json updated: version ${pkg.version}, ${skills.length} skill(s)`);
    }
  } else {
    console.log(`plugin.json in sync: version ${pkg.version}, ${skills.length} skill(s)`);
  }

  const unlisted = missingFromReadme(readFileSync(join(repo, "README.md"), "utf8"), skills);
  if (unlisted.length) problems.push(`README.md does not link: ${unlisted.join(", ")}. Add a row to the skills table.`);

  problems.forEach((problem) => console.error(`error: ${problem}`));
  return problems.length ? 1 : 0;
}

if (process.argv[1] && resolve(process.argv[1]) === new URL(import.meta.url).pathname) {
  const repoFlag = process.argv.indexOf("--repo");
  process.exit(run(process.argv.slice(2), repoFlag > -1 ? resolve(process.argv[repoFlag + 1]) : REPO));
}
