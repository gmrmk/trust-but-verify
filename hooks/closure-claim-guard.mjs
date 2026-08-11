// hooks/closure-claim-guard.mjs
//
// PreToolUse(Bash) HARD STOP on an unverified absolute closure claim in a git
// commit message. "Deleted", "fixed", "all clean", "no leftover", "100%" are
// single signals; they are claims until an independent second signal confirms
// them. This guard refuses a commit that asserts an absolute UNLESS the same
// message also names the proving signal (a grep that returned empty, an exit
// code, a re-fetch, a test output). It mechanizes the "one-signal done /
// over-claim closure" subversion - the shape of "deleted = safe."
//
// Contract: a PreToolUse hook that exits 2 blocks the tool and shows stderr to
// the model. Wire it in settings.json under hooks.PreToolUse for matcher Bash.

// NOTE on the shape: `100%` is matched by its own alternative WITHOUT a trailing
// \b. A word boundary after `%` requires a word character next, so `\b(100%)\b`
// never fires on "100% clean" - the `%` and the following space are both
// non-word. scripts/test_hooks.mjs covers this case; keep it covered.
const ABSOLUTE =
  /100\s*%|\b(fully (sanitized|clean|fixed|removed|gone)|all (clean|gone|removed|fixed|sanitized|purged)|nothing (personal|left|remains)|no\s+pii( anywhere)?|zero pii|guaranteed|definitely (safe|clean|gone|removed)|verified safe|totally clean|completely (fixed|safe|clean|removed|purged)|never fails|cannot fail|is now safe|fully resolved)\b/i;

// A named second signal that turns an absolute into a verified claim.
const PROOF =
  /\b(grep|verified by|exit 0|exit code|returns? (empty|zero|0|404|none|nothing)|re-?checked|second signal|tested|test output|harness|confirmed by|ls-remote|api (returns|404)|sha-?256|content-?match|scorer|all green)\b/i;

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
  if (/\bgit\s+commit\b/.test(cmd) && ABSOLUTE.test(cmd) && !PROOF.test(cmd)) {
    const hit = cmd.match(ABSOLUTE)[0];
    process.stderr.write(
      `CLOSURE GUARD - HARD STOP. This commit message asserts an absolute ("${hit}") with no ` +
        "proving signal. An absolute closure claim is a single signal; it needs a second, " +
        "independent one - a grep that returns empty, an exit code, a re-fetch, a test output. " +
        "Name that signal in the message, or qualify the claim. This is the 'deleted = safe' " +
        "failure mode; the hook will not commit an unverified absolute.\n"
    );
    process.exit(2); // block the tool call
  }
  process.exit(0);
});
