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
| `closure-claim-guard.mjs` | PreToolUse (Bash) | Blocks (`exit 2`) a `git commit` whose message asserts an unqualified absolute ("all clean", "no PII", "100%", "fully removed", "deleted") UNLESS the same message names the proving signal (a grep that returned empty, an exit code, a re-fetch, a test output). Mechanizes the "deleted = safe" / one-signal-done failure. Defends AB-15/AB-16. |

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

## Wiring

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit|Bash",
        "hooks": [
          { "type": "command", "command": "node hooks/pii-guard.mjs" }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "node hooks/closure-claim-guard.mjs" }
        ]
      }
    ]
  }
}
```

For defense in depth, the same checks belong as a git `pre-commit` / `commit-msg`
hook that scans the staged diff and the commit message: an ungated commit path is
how a single bad write reaches a remote, and the closure-claim check is most
valuable exactly at the commit boundary it guards.
