#!/usr/bin/env node
// Install this clone's skills into local agent skill folders, by symlink (so `git pull` updates them) or copy.
// Only skills/<name>/ is linked, so development files in dev/ are never installed.
//
//   node scripts/install.mjs [--dest <dir>]... [--skill <name>]... [--copy] [--force] [--dry-run] [--uninstall]
//
// Default destinations: ~/.claude/skills (Claude Code) and ~/.agents/skills (Codex and other Agent Skills tools).

import { cpSync, existsSync, lstatSync, mkdirSync, readlinkSync, rmSync, symlinkSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { REPO, listSkills } from "./lib/skills.mjs";

export const DEFAULT_DESTS = [join(homedir(), ".claude", "skills"), join(homedir(), ".agents", "skills")];

/** Parse argv into options; repeated flags (--dest, --skill) accumulate. */
export function parseArgs(argv) {
  const opts = { dests: [], skills: [], copy: false, force: false, dryRun: false, uninstall: false };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === "--dest") opts.dests.push(resolve(argv[++i]));
    else if (arg === "--skill") opts.skills.push(argv[++i]);
    else if (arg === "--copy") opts.copy = true;
    else if (arg === "--force") opts.force = true;
    else if (arg === "--dry-run") opts.dryRun = true;
    else if (arg === "--uninstall") opts.uninstall = true;
    else throw new Error(`unknown option ${arg}`);
  }
  if (!opts.dests.length) opts.dests = DEFAULT_DESTS;
  return opts;
}

const kind = (path) => {
  try {
    return lstatSync(path).isSymbolicLink() ? "link" : "other";
  } catch {
    return "none";
  }
};

/** Whether `path` is a symlink that points into `repo`, i.e. one this script created. */
function linksIntoRepo(path, repo) {
  return kind(path) === "link" && resolve(dirname(path), readlinkSync(path)).startsWith(join(repo, "skills"));
}

/** Install or uninstall each selected skill in each destination. Returns the log lines it acted on. */
export function run(opts, repo = REPO) {
  const all = listSkills(repo);
  const unknown = opts.skills.filter((name) => !all.some((skill) => skill.name === name));
  if (unknown.length) throw new Error(`unknown skill(s): ${unknown.join(", ")}. Available: ${all.map((s) => s.name).join(", ")}`);
  const selected = opts.skills.length ? all.filter((skill) => opts.skills.includes(skill.name)) : all;
  const log = [];

  for (const dest of opts.dests) {
    if (!opts.dryRun && !opts.uninstall) mkdirSync(dest, { recursive: true });
    for (const skill of selected) {
      const target = join(dest, skill.name);
      const state = kind(target);

      if (opts.uninstall) {
        if (state === "none") continue;
        if (!linksIntoRepo(target, repo)) {
          log.push(`skipped ${target} (not a link into this clone)`);
          continue;
        }
        if (!opts.dryRun) rmSync(target);
        log.push(`removed ${target}`);
        continue;
      }

      const foreign = state === "other" || (state === "link" && !linksIntoRepo(target, repo));
      if (foreign && !opts.force) {
        log.push(`skipped ${target} (exists and is not a link into this clone; use --force to replace it)`);
        continue;
      }
      if (state !== "none" && !opts.dryRun) rmSync(target, { recursive: true, force: true });
      if (!opts.dryRun) {
        if (opts.copy) cpSync(skill.dir, target, { recursive: true });
        else symlinkSync(skill.dir, target, "dir");
      }
      log.push(`${opts.copy ? "copied" : "linked"} ${skill.name} -> ${target}`);
    }
  }
  return log;
}

if (process.argv[1] && resolve(process.argv[1]) === new URL(import.meta.url).pathname) {
  try {
    const opts = parseArgs(process.argv.slice(2));
    const log = run(opts);
    console.log((opts.dryRun ? ["(dry run)", ...log] : log).join("\n") || "nothing to do");
  } catch (error) {
    console.error(`error: ${error.message}`);
    process.exit(1);
  }
}
