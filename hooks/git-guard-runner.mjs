#!/usr/bin/env node
// hooks/git-guard-runner.mjs
//
// Git-side defense in depth. Feeds the staged diff (pre-commit) or the commit
// message (commit-msg) into the SAME hard-stop guards that gate Claude Code's
// tool calls - so a commit made OUTSIDE the assistant (a human, another tool, a
// script) still cannot ship a personal reference (AB-13), a secret (AB-14), or
// an unverified absolute closure claim (AB-15). The Claude-side PreToolUse hooks
// catch a bad write before it is staged; this catches anything that reached the
// index by another path. An ungated commit boundary is how one bad write reaches
// a remote.
//
// Single source of truth: this runner shells out to pii-guard.mjs /
// secret-scan-guard.mjs / closure-claim-guard.mjs in this same directory, so the
// patterns are defined once.
//
// Usage (from the .git/hooks/ shims):
//   node git-guard-runner.mjs pre-commit
//   node git-guard-runner.mjs commit-msg <path-to-COMMIT_EDITMSG>
//
// Exit 0 = allow. Exit 1 = block the commit (stderr explains which guard fired).
// Bypass, used deliberately, is `git commit --no-verify`.

import { spawnSync, execSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const HERE = dirname(fileURLToPath(import.meta.url));
const mode = process.argv[2];

// Run one guard with a Claude-Code-shaped PreToolUse payload. The guard exits 2
// to block; anything else passes.
function runGuard(file, payload) {
  const r = spawnSync("node", [join(HERE, file)], {
    input: JSON.stringify(payload),
    encoding: "utf8",
  });
  if (r.status === 2) {
    process.stderr.write("\n" + (r.stderr || "").trim() + "\n");
    return false;
  }
  return true;
}

// Only the ADDED lines of a diff matter - a commit that REMOVES a secret or a
// personal reference must not be blocked for containing it on a `-` line.
function addedLines(diff) {
  return diff
    .split("\n")
    .filter((l) => l.startsWith("+") && !l.startsWith("+++"))
    .map((l) => l.slice(1))
    .join("\n");
}

let ok = true;

if (mode === "pre-commit") {
  let diff = "";
  try {
    diff = execSync("git diff --cached --no-color", {
      encoding: "utf8",
      maxBuffer: 64 * 1024 * 1024,
    });
  } catch {
    diff = ""; // huge or unreadable diff -> the Claude-side per-write guards already ran
  }
  const added = addedLines(diff);
  if (added.trim()) {
    if (!runGuard("pii-guard.mjs", { tool_input: { content: added } })) ok = false;
    if (!runGuard("secret-scan-guard.mjs", { tool_input: { content: added } }))
      ok = false;
  }
} else if (mode === "commit-msg") {
  const msgPath = process.argv[3];
  let msg = "";
  try {
    msg = readFileSync(msgPath, "utf8");
  } catch {
    msg = "";
  }
  // Drop git's comment lines and anything below a verbose-diff scissors marker.
  const body = msg
    .split("\n")
    .filter((l) => !l.startsWith("#") && !/^\s*-+\s*>8\s*-+/.test(l))
    .join("\n");
  if (body.trim()) {
    if (!runGuard("pii-guard.mjs", { tool_input: { content: body } })) ok = false;
    if (!runGuard("secret-scan-guard.mjs", { tool_input: { content: body } }))
      ok = false;
    // closure-claim-guard keys on a command containing `git commit`.
    if (
      !runGuard("closure-claim-guard.mjs", {
        tool_input: { command: `git commit -m ${JSON.stringify(body)}` },
      })
    )
      ok = false;
  }
} else {
  process.stderr.write(`git-guard-runner: unknown mode "${mode}"\n`);
  process.exit(0); // a wiring bug must not block every commit
}

if (!ok) {
  process.stderr.write(
    "\nCommit blocked by trust-but-verify git guards (above). Fix the flagged " +
      "content and re-commit. Deliberate bypass: git commit --no-verify\n"
  );
  process.exit(1);
}
process.exit(0);
