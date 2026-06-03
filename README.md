# trust-but-verify

A Socratic audit-and-repair skill for code artifacts. It walks a codebase one
finding at a time, asking - never asserting - until every load-bearing claim has
a second, independent signal. It is not a linter and not a substitute for a
professional audit; it is a phased dialogue that surfaces grounded findings and
lets you decide what to do with each one.

## What it does

- Scans a code artifact for unverified load-bearing claims and common
  trust-and-safety issues across six categories: security, privacy, license,
  accessibility, supply chain, operational.
- Enforces a two-signal verification gate on every finding. No finding ships
  without an independent, authoritative, falsifiable second signal.
- Presents survivors one at a time through `AskUserQuestion` option chips (not a
  wall of text), with a root-cause framework offered before any fix on
  HIGH/CRITICAL findings.
- Cites a real, current authoritative source (OWASP, NIST, WCAG, GDPR, SPDX,
  MITRE CWE) for every check - no fabricated grounding.
- Ships a labeled synthetic `test-corpus/` that measures both precision AND
  recall, with two harnesses (`score.py`, `verify_score.py`) that keep the
  corpus honest about its own detection.

See `trust-but-verify/SKILL.md` for the full specification.

## Install

### macOS / Linux

```bash
git clone https://github.com/gmrmk/trust-but-verify.git
cp -r trust-but-verify/trust-but-verify ~/.claude/skills/
```

### Windows (PowerShell)

```powershell
git clone https://github.com/gmrmk/trust-but-verify.git
Copy-Item -Path .\trust-but-verify\trust-but-verify -Destination "$env:USERPROFILE\.claude\skills\" -Recurse
```

## Usage

Once installed, `trust-but-verify` appears in Claude Code's `available-skills`
list. Invoke it from a session:

```
/trust-but-verify [path]
```

`path` defaults to the current directory. The skill walks four phases: Orient,
Scan, Walk-through, Capture. `SKILL.md` documents each phase, the verification
gate, the dialogue protocol, the anti-behavior defenses, and how to edit the
decision tree (`trust-tree.yaml`).

## The discipline

Every uncertainty routes through one funnel:

1. State the claim.
2. Name the second signal (independent, authoritative, falsifiable).
3. Verify against it.
4. Act, with the verified claim recorded.

The discipline applies recursively - the skill audits itself before any release,
and the `test-corpus/` harnesses run the skill's own detection patterns against
labeled fixtures so the labels can never quietly drift from what the detector
actually does.

## Hooks

`hooks/` ships a hard-stop guard:

- `pii-guard.mjs` - a `PreToolUse` guard that exits `2` (blocks the tool) when a
  write or command contains a personal reference: a relationship attribution, a
  possessive tying a person to the user, or any term on `hooks/pii-denylist.txt`.
  Personal data must never enter a committed or published artifact. Wire it in
  `.claude/settings.json` under `hooks.PreToolUse` for the `Write|Edit|MultiEdit|Bash`
  matchers. See `hooks/README.md`.

## Sibling skills

- **dual-log-memory** - a memory architecture (a fix log for what broke, an
  insight log for what worked). https://github.com/gmrmk/dual-log-memory
- **ai-pairing-playbook** - a reciprocal prompting reference for sustained
  LLM-assisted work. https://github.com/gmrmk/ai-pairing-playbook

## License

MIT - see `LICENSE`. The license carries a non-substitute disclaimer: this skill
surfaces issues and cites frameworks; it is not legal advice and not a compliance
certification.

## Contributing

Issues and PRs welcome. The skill improves through its own discipline: if a check
fires wrongly, or misses something a senior reviewer would catch, open an issue
describing the false positive or the recall gap, ideally with a labeled
`test-corpus/` case that reproduces it.
