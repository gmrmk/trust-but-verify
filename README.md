# trust-but-verify

[![CI](https://github.com/gmrmk/trust-but-verify/actions/workflows/ci.yml/badge.svg)](https://github.com/gmrmk/trust-but-verify/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A Socratic audit-and-repair skill for code artifacts. It walks a codebase one
finding at a time, asking - never asserting - until every load-bearing claim has
a second, independent signal. It is not a linter and not a substitute for a
professional audit; it is a phased dialogue that surfaces grounded findings and
lets you decide what to do with each one.

## What it does

- Scans a code artifact for unverified load-bearing claims and common
  trust-and-safety issues across six categories: security, privacy, license,
  accessibility, supply chain, operational - plus an epistemic category carrying
  the original doctrine.
- Enforces a two-signal verification gate on every finding. No finding ships
  without an independent, authoritative, falsifiable second signal.
- Presents survivors one at a time through `AskUserQuestion` option chips (not a
  wall of text), with a root-cause framework offered before any fix on
  HIGH/CRITICAL findings.
- Cites a real, current authoritative source (OWASP, NIST, WCAG, GDPR, SPDX,
  MITRE CWE) for every check - no fabricated grounding.
- Ships a labeled synthetic `test-corpus/` that measures both precision AND
  recall, with three harnesses that keep the corpus honest about its own
  detection.

See `skills/trust-but-verify/SKILL.md` for the full specification.

## Install

### As a plugin (recommended)

From inside Claude Code:

```
/plugin marketplace add gmrmk/trust-but-verify
/plugin install trust-but-verify@gmrmk-skills
```

The skill then appears as `/trust-but-verify:trust-but-verify`. Update later
with `/plugin marketplace update gmrmk-skills`.

Installing the plugin does **not** activate the hook guards - they are opt-in.
See [Hooks](#hooks).

### As a plain skill (manual copy)

**macOS / Linux**

```bash
git clone https://github.com/gmrmk/trust-but-verify.git
cp -r trust-but-verify/skills/trust-but-verify ~/.claude/skills/
```

**Windows (PowerShell)**

```powershell
git clone https://github.com/gmrmk/trust-but-verify.git
Copy-Item -Path .\trust-but-verify\skills\trust-but-verify -Destination "$env:USERPROFILE\.claude\skills\" -Recurse
```

The copied directory is the runtime payload only - `SKILL.md`, `trust-tree.yaml`,
and `references/`. The corpus and the harnesses stay in the repository, because
the fixtures are deliberately vulnerable code and belong nowhere near your
skills directory.

## Usage

Invoke it from a session:

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
and CI enforces the parts a reader could otherwise skip.

## Hooks

`hooks/` ships four hard-stop guards for Claude Code. They are **opt-in**: a
plugin install does not wire them, and nothing runs until you add them to
`.claude/settings.json` yourself.

| Guard | Blocks |
| --- | --- |
| `pii-guard.mjs` | A write or command that ties a person or role to the user, or matches a term in `pii-denylist.txt`. |
| `secret-scan-guard.mjs` | Credential material reaching a file or command - API keys, private-key blocks, credentials in a URL, hardcoded `password=` assignments. Never echoes the matched value. |
| `closure-claim-guard.mjs` | A `git commit` message asserting an unqualified absolute ("all clean", "100%") without naming the signal that proves it. |
| `irreversible-op-guard.mjs` | A destructive command (`rm -rf`, `git reset --hard`, force-push, SQL `DROP`) that does not name a rollback path. |

They are intentionally aggressive - a false stop costs seconds, a missed leak
costs someone their privacy. Read `hooks/README.md` for the wiring, the git-side
shims, and the rationale before enabling them.

## Development

```bash
python -m pip install -r requirements.txt

python test-corpus/score.py                       # detection-layer harness (regex branches)
python test-corpus/structural/score_structural.py  # structural harness (mini-repo branches)
python test-corpus/verify_score.py                 # full-pipeline scorer (designed metrics)
python scripts/check_branch_schema.py              # branch-schema gate
node   scripts/test_hooks.mjs                      # hook guard smoke tests
python scripts/check_citations.py                  # citation liveness (network)
```

The first five run in CI on every pull request and must be green. Citation
liveness runs weekly, on demand, and on release tags - not on pull requests, so
that a standards host having a bad afternoon never trains anyone to merge past a
red check.

Node 18+ is required for the hook guards (dependency-free ESM using `node:`
builtin specifiers). Python 3.9+ and PyYAML for the harnesses.

**Adding a branch** to `trust-tree.yaml` requires, and CI enforces: a `verify:`
step that is not a restatement of `detect:`, at least one `framework:` id from
the registry, a `liability_template:`, an `rca_defaults:` entry, and at least one
labeled `test-corpus/` case. A branch with no test case is an unmeasured claim.

## Sibling skills

- **dual-log-memory** - a memory architecture (a fix log for what broke, an
  insight log for what worked). https://github.com/gmrmk/dual-log-memory
- **ai-pairing-playbook** - a reciprocal prompting reference for sustained
  LLM-assisted work. https://github.com/gmrmk/ai-pairing-playbook

## Security

See `SECURITY.md` for private vulnerability reporting and what is in scope. In
short: a guard that fails to block what it documents is a vulnerability; a
detection false positive or false negative is a precision/recall bug - open a
normal issue with a labeled corpus case.

## License

MIT - see `LICENSE`. The license carries a non-substitute disclaimer: this skill
surfaces issues and cites frameworks; it is not legal advice and not a compliance
certification.

## Contributing

Issues and PRs welcome. The skill improves through its own discipline: if a check
fires wrongly, or misses something a senior reviewer would catch, open an issue
describing the false positive or the recall gap, ideally with a labeled
`test-corpus/` case that reproduces it. A case that turns a documented
`false_negative` into a `true_positive` is a recall promotion - the most valuable
kind of contribution here.
