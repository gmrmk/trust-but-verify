// hooks/irreversible-op-guard.mjs
//
// PreToolUse(Bash) HARD STOP on an irreversible / destructive operation run
// WITHOUT a named rollback path. Defends two anti-behaviors at once:
//
//   AB-16 (recovery-racing): after a flagged failure the reflex is to DO
//   something fast to restore competence. A destructive op fired under that
//   urgency - reset --hard, force-push, rm -rf - is how the cleanup destroys
//   the evidence or re-introduces the fault. Speed during recovery is the tell.
//
//   AB-17 (volume-as-diligence): the bigger and more impressive the change, the
//   more likely the one basic check was skipped. The gate is STRUCTURAL, not a
//   judgment made when "feeling done" - and destructive / force / irreversible
//   ops earn MORE scrutiny, not less. Impressiveness buys no pass.
//
// The rule: a destructive op is blocked UNLESS the same command names a rollback
// or safety net (a backup, a stash, a tag, a dry-run, --force-with-lease,
// reflog, a copy). State the rollback path BEFORE you run the op, or do not run
// it. This is the two-safety-net pattern as a hard stop.
//
// Contract: a PreToolUse hook that exits 2 blocks the tool and shows stderr to
// the model. Wire under hooks.PreToolUse for matcher Bash.

const DESTRUCTIVE = [
  ["git reset --hard", /\bgit\s+reset\s+--hard\b/],
  ["git push --force", /\bgit\s+push\b[^\n]*(?:--force\b|\s-f\b)/],
  ["git branch -D (force delete)", /\bgit\s+branch\s+-D\b/],
  ["git clean -f (force)", /\bgit\s+clean\s+-[a-zA-Z]*f/],
  ["remote branch delete", /\bgit\s+push\s+\S+\s+:[^\s]/],
  ["rm -rf", /\brm\s+-[a-zA-Z]*r[a-zA-Z]*f|\brm\s+-[a-zA-Z]*f[a-zA-Z]*r|\s-rf\b|\s-fr\b/],
  ["Remove-Item -Recurse -Force", /Remove-Item\b[^\n]*-Recurse[^\n]*-Force|Remove-Item\b[^\n]*-Force[^\n]*-Recurse/i],
  ["SQL DROP/TRUNCATE", /\b(?:DROP|TRUNCATE)\s+(?:TABLE|DATABASE|SCHEMA)\b/i],
];

// A named safety net that turns an irreversible op into a recoverable one.
// --force-with-lease is the safe force (it refuses to clobber unseen work), so
// it counts as its own rollback signal.
const ROLLBACK =
  /\b(backup|\.bak\b|git\s+stash|git\s+tag\b|snapshot|--dry-run|reflog|force-with-lease|cp\s+-|copy-item)\b/i;

let raw = "";
process.stdin.on("data", (c) => (raw += c));
process.stdin.on("end", () => {
  let j = {};
  try {
    j = JSON.parse((raw.charCodeAt(0) === 0xfeff ? raw.slice(1) : raw).trim());
  } catch {
    process.exit(0);
  }

  const cmd = String((j.tool_input || {}).command || "");
  if (!cmd) process.exit(0);

  for (const [label, re] of DESTRUCTIVE) {
    if (re.test(cmd) && !ROLLBACK.test(cmd)) {
      process.stderr.write(
        `IRREVERSIBLE-OP GUARD - HARD STOP. This command runs a destructive / ` +
          `irreversible operation ("${label}") with no named rollback path. After a ` +
          "failure the reflex to act fast is exactly how cleanup destroys evidence " +
          "(AB-16); and a big or destructive change earns MORE scrutiny, not less " +
          "(AB-17). Name the safety net in the command first - an independent backup, " +
          "a git stash or tag, a dry-run, --force-with-lease, or a copy - then retry. " +
          "State the rollback path before you run the op, or do not run it.\n"
      );
      process.exit(2); // block the tool call
    }
  }
  process.exit(0);
});
