// hooks/secret-scan-guard.mjs
//
// PreToolUse(Write|Edit|MultiEdit|Bash) HARD STOP on a secret reaching the
// publish surface. Defends AB-14: inward-only verification - the auditor runs
// many checks that confirm INTERNAL consistency (corpus matches labels, harness
// is green) and never the OUTWARD question of what actually ships. This guard is
// the outward check: it scans the exact bytes about to be written (file content)
// or run (command text) for credential material and refuses the write BEFORE the
// secret can be staged, committed, or pushed.
//
// Per AB-5, a matched secret is NEVER echoed back - the block names the TYPE and
// a redacted length only, so the guard's own output cannot become the leak.
//
// Contract: a PreToolUse hook that exits 2 blocks the tool and shows stderr to
// the model. Wire under hooks.PreToolUse for matchers Write|Edit and Bash.

// Each pattern is [label, regex]. Narrow by construction - precision over recall
// here is deliberate: a false stop costs seconds, but a false-positive STORM
// that blocks every legitimate write is its own anti-pattern (it trains the
// operator to disable the guard). Bare base64 / hex blobs are intentionally
// excluded; they collide with hashes and IDs.
const SECRET_PATTERNS = [
  ["OpenAI key", /\bsk-[A-Za-z0-9_-]{20,}\b/],
  ["Anthropic key", /\bsk-ant-[A-Za-z0-9_-]{20,}\b/],
  ["AWS access key id", /\bAKIA[0-9A-Z]{16}\b/],
  ["GitHub token", /\bgh[pousr]_[A-Za-z0-9]{36,}\b/],
  ["Slack token", /\bxox[bpars]-[A-Za-z0-9-]{10,}\b/],
  ["Google API key", /\bAIza[0-9A-Za-z_-]{35}\b/],
  ["private key block", /-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----/],
  ["credentials in URL", /\bhttps?:\/\/[^/\s:@]+:[^/\s@]+@/],
  [
    "hardcoded credential assignment",
    /\b(?:secret|token|passwd|password|api[_-]?key|access[_-]?key|client[_-]?secret)\s*[:=]\s*['"][^'"]{6,}['"]/i,
  ],
];

function collect(j) {
  const ti = j.tool_input || {};
  const parts = [];
  if (typeof ti.content === "string") parts.push(ti.content);
  if (typeof ti.new_string === "string") parts.push(ti.new_string);
  if (Array.isArray(ti.edits)) {
    for (const e of ti.edits)
      if (e && typeof e.new_string === "string") parts.push(e.new_string);
  }
  if (typeof ti.command === "string") parts.push(ti.command);
  return parts.join("\n");
}

let raw = "";
process.stdin.on("data", (c) => (raw += c));
process.stdin.on("end", () => {
  let j = {};
  try {
    j = JSON.parse((raw.charCodeAt(0) === 0xfeff ? raw.slice(1) : raw).trim());
  } catch {
    process.exit(0);
  }

  const text = collect(j);
  for (const [label, re] of SECRET_PATTERNS) {
    const m = text.match(re);
    if (m) {
      process.stderr.write(
        `SECRET SCAN - HARD STOP. The bytes about to ship contain a ${label} ` +
          `(${m[0].length} chars, value withheld). Internal harness-green is not ` +
          "publish-safety: a credential reaching a file, commit, or push is the " +
          "outward failure this guard exists to stop. Remove the secret, move it to " +
          "an environment variable or secret manager, and retry. The guard will not " +
          "write credential material on your behalf.\n"
      );
      process.exit(2); // block the tool call
    }
  }
  process.exit(0);
});
