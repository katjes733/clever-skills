// Tests for the repo tooling: skill discovery, plugin sync, and the local installer.
// Each test builds a throwaway repo in a temp dir, so nothing touches the real clone or home directory.

import assert from "node:assert/strict";
import { existsSync, lstatSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { parseArgs, run as install } from "../install.mjs";
import { listSkills, parseFrontmatter } from "../lib/skills.mjs";
import { missingFromReadme, run as sync } from "../sync-plugin.mjs";

function fakeRepo(skillNames, { readmeLinks = skillNames, version = "1.2.3" } = {}) {
  const repo = mkdtempSync(join(tmpdir(), "clever-skills-"));
  for (const name of skillNames) {
    mkdirSync(join(repo, "skills", name), { recursive: true });
    writeFileSync(join(repo, "skills", name, "SKILL.md"), `---\nname: ${name}\ndescription: Does ${name}\n---\n# ${name}\n`);
  }
  mkdirSync(join(repo, ".claude-plugin"));
  writeFileSync(join(repo, ".claude-plugin", "plugin.json"), JSON.stringify({ name: "p", version: "0.0.0", skills: [] }, null, 2) + "\n");
  writeFileSync(join(repo, "package.json"), JSON.stringify({ name: "p", version }));
  writeFileSync(join(repo, "README.md"), readmeLinks.map((n) => `[${n}](skills/${n})`).join("\n"));
  return repo;
}

const quiet = (fn) => {
  const { log, error } = console;
  console.log = console.error = () => {};
  try {
    return fn();
  } finally {
    Object.assign(console, { log, error });
  }
};

test("parseFrontmatter reads name and description, and rejects a missing block", () => {
  assert.deepEqual(parseFrontmatter('---\nname: a\ndescription: "b c"\n---\nbody'), { name: "a", description: "b c" });
  assert.throws(() => parseFrontmatter("no frontmatter"));
});

test("listSkills finds skills in name order and rejects a folder/name mismatch", () => {
  const repo = fakeRepo(["zeta", "alpha"]);
  assert.deepEqual(listSkills(repo).map((s) => s.name), ["alpha", "zeta"]);
  writeFileSync(join(repo, "skills", "zeta", "SKILL.md"), "---\nname: other\ndescription: x\n---\n");
  assert.throws(() => listSkills(repo), /must equal the folder name/);
});

test("sync writes every skill and the package version into plugin.json, and --check then passes", () => {
  const repo = fakeRepo(["beta", "alpha"]);
  assert.equal(quiet(() => sync(["--check"], repo)), 1);
  assert.equal(quiet(() => sync([], repo)), 0);
  const plugin = JSON.parse(readFileSync(join(repo, ".claude-plugin", "plugin.json"), "utf8"));
  assert.equal(plugin.version, "1.2.3");
  assert.deepEqual(plugin.skills, ["./skills/alpha", "./skills/beta"]);
  assert.equal(quiet(() => sync(["--check"], repo)), 0);
});

test("sync --check fails when a skill is missing from the README", () => {
  const repo = fakeRepo(["alpha", "beta"], { readmeLinks: ["alpha"] });
  quiet(() => sync([], repo));
  assert.equal(quiet(() => sync(["--check"], repo)), 1);
  assert.deepEqual(missingFromReadme("[a](skills/alpha)", [{ name: "alpha" }, { name: "beta" }]), ["beta"]);
});

test("install links skills, skips real directories unless forced, and uninstall removes only its own links", () => {
  const repo = fakeRepo(["alpha", "beta"]);
  const dest = mkdtempSync(join(tmpdir(), "dest-"));
  const opts = (extra) => parseArgs(["--dest", dest, ...extra]);

  install(opts([]), repo);
  assert.ok(lstatSync(join(dest, "alpha")).isSymbolicLink());
  assert.ok(existsSync(join(dest, "beta", "SKILL.md")));

  install(opts([]), repo); // idempotent
  assert.ok(lstatSync(join(dest, "alpha")).isSymbolicLink());

  const own = join(dest, "gamma");
  mkdirSync(own);
  writeFileSync(join(own, "keep.txt"), "mine");
  assert.deepEqual(install(opts(["--skill", "alpha"]), repo).length, 1);

  install(opts(["--uninstall"]), repo);
  assert.equal(existsSync(join(dest, "alpha")), false);
  assert.ok(existsSync(join(own, "keep.txt")), "unrelated directory untouched");
});

test("install refuses to replace a real directory without --force, and copies with --copy", () => {
  const repo = fakeRepo(["alpha"]);
  const dest = mkdtempSync(join(tmpdir(), "dest-"));
  mkdirSync(join(dest, "alpha"));
  writeFileSync(join(dest, "alpha", "mine.txt"), "mine");

  assert.match(install(parseArgs(["--dest", dest]), repo)[0], /skipped/);
  assert.ok(existsSync(join(dest, "alpha", "mine.txt")));

  install(parseArgs(["--dest", dest, "--copy", "--force"]), repo);
  assert.equal(lstatSync(join(dest, "alpha")).isSymbolicLink(), false);
  assert.ok(existsSync(join(dest, "alpha", "SKILL.md")));
});

test("install --dry-run changes nothing, and an unknown skill is an error", () => {
  const repo = fakeRepo(["alpha"]);
  const dest = join(mkdtempSync(join(tmpdir(), "dest-")), "skills");
  install(parseArgs(["--dest", dest, "--dry-run"]), repo);
  assert.equal(existsSync(dest), false);
  assert.throws(() => install(parseArgs(["--dest", dest, "--skill", "nope"]), repo), /unknown skill/);
});
