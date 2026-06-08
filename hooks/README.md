# Hooks

A hard-stop guard for Claude Code. The `.mjs` hook reads the Claude Code hook
payload from stdin and runs at a defined point in the tool lifecycle. It runs
under Node.js.

Wire it in `.claude/settings.json` under the matching `hooks` section. You can
review or disable it from the `/hooks` menu.

## Hook reference

| Hook | Trigger | What it enforces |
| --- | --- | --- |
| `pii-guard.mjs` | PreToolUse (Write/Edit/MultiEdit/Bash) | Blocks (`exit 2`) any file write or command whose text contains a personal-reference / role-attribution pattern - a possessive pronoun that ties a relation or a role to the user - or any term on `pii-denylist.txt`. Personal data must never enter a committed or published artifact. Bare technical nouns (`parent`, `child`, `bilateral`) are not blocked; only the attribution shape is. Defends AB-13. |
| `secret-scan-guard.mjs` | PreToolUse (Write/Edit/MultiEdit/Bash) | Blocks (`exit 2`) a write or command whose bytes contain credential material - OpenAI/Anthropic/AWS/GitHub/Slack/Google keys, private-key blocks, credentials in a URL, or a hardcoded `secret=`/`password=` assignment. The matched value is never echoed back (only its type and length), so the guard's own output can't become the leak. This is the OUTWARD publish-safety check - internal harness-green is not the same as safe-to-ship. Defends AB-14. |
| `closure-claim-guard.mjs` | PreToolUse (Bash) | Blocks (`exit 2`) a `git commit` whose message asserts an unqualified absolute ("all clean", "no PII", "100%", "fully removed", "deleted") UNLESS the same message names the proving signal (a grep that returned empty, an exit code, a re-fetch, a test output). Mechanizes the "deleted = safe" / one-signal-done failure. Defends AB-15/AB-16. |
| `irreversible-op-guard.mjs` | PreToolUse (Bash) | Blocks (`exit 2`) a destructive / irreversible command - `git reset --hard`, force-push, `git branch -D`, `git clean -f`, `rm -rf`, `Remove-Item -Recurse -Force`, SQL `DROP`/`TRUNCATE` - UNLESS the command names a rollback path (a backup, `git stash`, a tag, a dry-run, `--force-with-lease`, a copy). State the safety net before the op, or it does not run. Destructive changes earn more scrutiny, not less. Defends AB-16/AB-17. |

## Why this exists

Personal data leaking into a published artifact - a commit message, a branch
name, a session log, a skill file - is a quiet, high-cost failure: it looks
finished, trips no alarm, and the person trusting the output ships the liability
without knowing. This guard is the forcing function that makes that leak a hard
stop rather than a judgment call. The asymmetry is deliberate: a false stop costs
a few seconds; a missed leak costs a person their privacy. So it blocks
aggressively - a possessive that attaches a relation or a role to the user is
refused before the bytes are written.

## `pii-denylist.txt`

One term per line, case-insensitive substring match. Add the specific names,
handles, or initials you never want in a published artifact. Keep this file
gitignored if the terms themselves are sensitive.

## Anti-behavior coverage

The four guards mechanize the CRITICAL/HIGH personal-safety anti-behaviors from
`../trust-but-verify/references/anti-behaviors.md`. Each is a structural hard stop,
not a judgment the author makes when "feeling done":

| Anti-behavior | Hard-stop guard |
| --- | --- |
| AB-13 personal-reference (PII) leakage | `pii-guard.mjs` |
| AB-14 inward-only verification (secret reaches the publish surface) | `secret-scan-guard.mjs` |
| AB-15 one-signal closure ("deleted = safe") | `closure-claim-guard.mjs` |
| AB-16 recovery-racing | the guards fire with no "but I'm fixing it" exemption, plus `irreversible-op-guard.mjs` |
| AB-17 volume-as-diligence (destructive ops earn more scrutiny) | `irreversible-op-guard.mjs` |

AB-16 has no dedicated file because its defense is that the *other* guards keep
firing during recovery - the cleanup is exactly when a re-leak is most likely, so
there is no relaxed path. `irreversible-op-guard.mjs` adds the "back up before you
mutate" half.

## Wiring

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit|Bash",
        "hooks": [
          { "type": "command", "command": "node hooks/pii-guard.mjs" },
          { "type": "command", "command": "node hooks/secret-scan-guard.mjs" }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "node hooks/closure-claim-guard.mjs" },
          { "type": "command", "command": "node hooks/irreversible-op-guard.mjs" }
        ]
      }
    ]
  }
}
```

## Git-side defense in depth

The Claude Code hooks above gate the *assistant's* tool calls. A commit made
outside the assistant - by a human, another tool, or a script - bypasses them.
The git hooks close that gap by running the same guards at the commit boundary,
where a single bad write would otherwise reach a remote.

`git-guard-runner.mjs` is the shared shim. It feeds the staged diff (pre-commit)
or the commit message (commit-msg) into the same `pii-guard` / `secret-scan-guard`
/ `closure-claim-guard` so the patterns stay single-source. It only scans ADDED
lines, so a commit that *removes* a secret or a personal reference is never
blocked for containing it.

Sample shims live in `hooks/git/`. Adjust the runner path inside each shim to
wherever the guards live - `hooks/` in this repo's layout, or `.claude/hooks/` in
a Claude Code project.

### Recommended: tracked `.githooks/` (travels with clones)

`.git/hooks/` is never committed, so hooks copied there protect only your local
clone. Point `core.hooksPath` at a tracked dir instead, and the hooks ship with
the repo:

```sh
mkdir -p .githooks
cp hooks/git/pre-commit hooks/git/commit-msg hooks/git/install.sh .githooks/
chmod +x .githooks/pre-commit .githooks/commit-msg .githooks/install.sh
git add .githooks
git config core.hooksPath .githooks          # activate (see caveat below)
```

`core.hooksPath` is local config and is NOT cloned, so every fresh clone runs the
activation once - `git config core.hooksPath .githooks` (or `sh .githooks/install.sh`).
The cost of the model: until a clone activates, NO git hooks run. With a Node
project you can automate it by adding `"prepare": "git config core.hooksPath .githooks"`
to `package.json` so `npm install` does it.

### Alternative: copy into `.git/hooks/` (simple, local only)

```sh
cp hooks/git/pre-commit  .git/hooks/pre-commit
cp hooks/git/commit-msg  .git/hooks/commit-msg
chmod +x .git/hooks/pre-commit .git/hooks/commit-msg
```

If a `pre-commit` hook already exists (either model), chain the runner into it
rather than overwrite - keep the existing checks, then add:

```sh
runner="$(git rev-parse --show-toplevel)/.claude/hooks/git-guard-runner.mjs"
[ -f "$runner" ] && { node "$runner" pre-commit || exit 1; }
```

Deliberate bypass, when a block is a confirmed false positive, is
`git commit --no-verify`. The closure-claim check is most valuable exactly at
this commit boundary.
