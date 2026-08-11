// scripts/test_hooks.mjs
//
// Smoke tests for the four hard-stop guards in hooks/.
//
// WHY THIS EXISTS
// ---------------
// hooks/README.md documents what each guard blocks. Documentation of a guard is
// not evidence the guard fires - a regex that silently stops matching still has
// a README saying it blocks. These tests are the second signal on the guards
// themselves: each case feeds a real Claude Code hook payload over stdin and
// asserts the exit code (2 = blocked, 0 = allowed).
//
// They are hermetic - no network, no git, no filesystem writes - so they belong
// in the pull-request gate.
//
// USAGE:  node scripts/test_hooks.mjs
// EXIT:   0 if every case behaves as documented, 1 otherwise.

import { spawnSync } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const HOOKS = join(ROOT, "hooks");

const BLOCK = 2;
const ALLOW = 0;

/**
 * Each case: [guard, description, toolInput, expectedExit, extraAssert?]
 * extraAssert receives stderr and returns an error string, or null when it passes.
 */
const CASES = [
  // ── pii-guard ───────────────────────────────────────────────────────────
  ["pii-guard.mjs", "blocks a relation tied to the user in file content",
    { content: "Reviewed this with my brother over the weekend." }, BLOCK],
  ["pii-guard.mjs", "blocks a role attribution in a command",
    { command: 'git commit -m "applied the fix my manager suggested"' }, BLOCK],
  ["pii-guard.mjs", "blocks an attribution inside a MultiEdit edit",
    { edits: [{ old_string: "x", new_string: "credit to their colleague" }] }, BLOCK],
  ["pii-guard.mjs", "allows a bare technical noun with no attribution",
    { content: "The parent process spawns a child process; both exit cleanly." }, ALLOW],
  ["pii-guard.mjs", "allows text matching a COMMENTED-OUT denylist line",
    { content: "Jane Doe is an example name in the denylist comments." }, ALLOW],
  ["pii-guard.mjs", "allows ordinary prose",
    { content: "Refactored the scorer to resolve trust-tree.yaml explicitly." }, ALLOW],

  // ── secret-scan-guard ───────────────────────────────────────────────────
  ["secret-scan-guard.mjs", "blocks an AWS access key id",
    { content: "AWS_KEY = 'AKIAIOSFODNN7EXAMPLE'" }, BLOCK],
  ["secret-scan-guard.mjs", "blocks a private key block",
    { content: "-----BEGIN RSA PRIVATE KEY-----\nMIIEow==\n" }, BLOCK],
  ["secret-scan-guard.mjs", "blocks credentials embedded in a URL",
    { command: "curl https://admin:hunter2hunter2@internal.example.com/api" }, BLOCK],
  ["secret-scan-guard.mjs", "blocks a hardcoded password assignment",
    { content: 'password = "s3cret-value-here"' }, BLOCK],
  ["secret-scan-guard.mjs", "allows an env-var reference",
    { content: 'password = os.environ["APP_PASSWORD"]' }, ALLOW],
  ["secret-scan-guard.mjs", "allows a bare hex digest (not a credential)",
    { content: "sha256 = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'" }, ALLOW],
  // AB-5: the guard's own output must never become the leak.
  ["secret-scan-guard.mjs", "never echoes the matched secret back (AB-5)",
    { content: "AWS_KEY = 'AKIAIOSFODNN7EXAMPLE'" }, BLOCK,
    (stderr) => stderr.includes("AKIAIOSFODNN7EXAMPLE")
      ? "stderr echoed the matched secret value"
      : null],

  // ── closure-claim-guard ─────────────────────────────────────────────────
  ["closure-claim-guard.mjs", "blocks an absolute closure claim with no proof",
    { command: 'git commit -m "all clean now"' }, BLOCK],
  ["closure-claim-guard.mjs", "blocks a 100% claim with no proof",
    { command: 'git commit -m "100% of findings resolved"' }, BLOCK],
  ["closure-claim-guard.mjs", "allows an absolute that names its proving signal",
    { command: 'git commit -m "all clean - grep returns empty, harness exit 0"' }, ALLOW],
  ["closure-claim-guard.mjs", "allows a qualified claim",
    { command: 'git commit -m "removed the flagged strings from the two files"' }, ALLOW],
  ["closure-claim-guard.mjs", "ignores an absolute outside a git commit",
    { command: 'echo "all clean"' }, ALLOW],

  // ── irreversible-op-guard ───────────────────────────────────────────────
  ["irreversible-op-guard.mjs", "blocks rm -rf with no rollback named",
    { command: "rm -rf build/" }, BLOCK],
  ["irreversible-op-guard.mjs", "blocks git reset --hard with no rollback named",
    { command: "git reset --hard origin/main" }, BLOCK],
  ["irreversible-op-guard.mjs", "blocks a bare force-push",
    { command: "git push --force origin main" }, BLOCK],
  ["irreversible-op-guard.mjs", "blocks SQL DROP TABLE",
    { command: 'psql -c "DROP TABLE users"' }, BLOCK],
  ["irreversible-op-guard.mjs", "allows a force-push with --force-with-lease",
    { command: "git push --force-with-lease origin main" }, ALLOW],
  ["irreversible-op-guard.mjs", "allows a destructive op that names a backup",
    { command: "cp -r build/ build.bak && rm -rf build/" }, ALLOW],
  ["irreversible-op-guard.mjs", "allows a non-destructive command",
    { command: "git status --short" }, ALLOW],
];

function run(guard, toolInput) {
  const r = spawnSync(process.execPath, [join(HOOKS, guard)], {
    input: JSON.stringify({ tool_input: toolInput }),
    encoding: "utf8",
  });
  if (r.error) throw r.error;
  return { code: r.status, stderr: r.stderr || "" };
}

let failed = 0;
let passed = 0;

console.log("=".repeat(78));
console.log("HOOK GUARD SMOKE TESTS");
console.log("=".repeat(78));

let currentGuard = "";
for (const [guard, desc, toolInput, expected, extraAssert] of CASES) {
  if (guard !== currentGuard) {
    currentGuard = guard;
    console.log(`\n  ${guard}`);
  }
  const { code, stderr } = run(guard, toolInput);
  const want = expected === BLOCK ? "block" : "allow";
  const got = code === BLOCK ? "block" : code === ALLOW ? "allow" : `exit ${code}`;

  let problem = code === expected ? null : `expected ${want}, got ${got}`;
  if (!problem && extraAssert) problem = extraAssert(stderr);
  // A blocking guard must explain itself to the model, or the block is opaque.
  if (!problem && expected === BLOCK && stderr.trim() === "") {
    problem = "blocked without writing an explanation to stderr";
  }

  if (problem) {
    failed++;
    console.log(`    FAIL  ${desc}\n          ${problem}`);
  } else {
    passed++;
    console.log(`    ok    ${desc}`);
  }
}

console.log("\n" + "=".repeat(78));
if (failed) {
  console.log(`RESULT: ${failed} failing, ${passed} passing.`);
  process.exit(1);
}
console.log(`RESULT: all ${passed} guard cases behave as hooks/README.md documents. [PASS]`);
