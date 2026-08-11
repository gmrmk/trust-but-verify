# Security Policy

## Reporting a vulnerability

Report suspected vulnerabilities through GitHub's private reporting channel:

**[Open a private security advisory](https://github.com/gmrmk/trust-but-verify/security/advisories/new)**

Please do not open a public issue for a suspected vulnerability. Private
reporting keeps the details out of public view until a fix is available.

Include, where you can:

- what the issue is and which file or component it affects
- how to reproduce it (a labeled `test-corpus/` case is ideal — see below)
- what an attacker could do with it
- any version, OS, or Node/Python details that matter

**Response expectations.** This is a small, volunteer-maintained project with no
paid on-call. Expect an acknowledgement within about a week. There is no bounty
program. If you have had no response in two weeks, feel free to nudge by opening
a public issue that says only that a private report is pending — no details.

## Supported versions

Only the latest release receives fixes. There are no long-term-support branches.

## Scope

This repository ships a Claude Code skill (prose + a decision tree), a labeled
synthetic corpus, and four Node hook guards. What counts as a vulnerability here
is narrower than for a running service:

**In scope**

- A hook guard failing to block what `hooks/README.md` says it blocks — for
  example, a secret shape that reaches a file or commit past
  `secret-scan-guard.mjs`, or a personal reference past `pii-guard.mjs`.
- A guard that leaks the thing it caught. The guards must name the *type* and
  length of a matched secret and never echo its value (anti-behavior AB-5).
  Covered by a test in `scripts/test_hooks.mjs`; a regression is a real bug.
- Content in `SKILL.md`, `trust-tree.yaml`, or `references/` that could steer an
  auditing agent into an unsafe action.
- Anything in the skill that would cause an audit report to write unredacted
  secrets or personal data to disk.

**Out of scope**

- The deliberately vulnerable fixtures under `test-corpus/`. Every one of them
  is intentional, labeled in a manifest, and non-executable in place. The
  secret-shaped strings there are documented placeholders, not live credentials
  (for example, AWS's own published example key ID). Reports that the corpus
  "contains vulnerabilities" will be closed as working-as-designed.
- The guard-trigger payloads in `scripts/test_hooks.mjs`. A test that proves
  `secret-scan-guard.mjs` blocks an AWS key must contain a string shaped like an
  AWS key, and a test that proves `pii-guard.mjs` blocks a role attribution must
  contain one. Same for the fixture above.
- False positives and false negatives in detection. Those are **recall and
  precision bugs**, not security vulnerabilities — open a normal issue with a
  labeled corpus case, per the contributing note in `README.md`. The corpus
  exists to make exactly that argument measurable.
- Vulnerabilities in a codebase this skill audited. The skill surfaces findings;
  it does not certify anything. See the disclaimer in `LICENSE`.

## What this project is not

`trust-but-verify` is a self-assessment and diligence aid. It is not a
penetration test, not a compliance certification, and not legal advice. See the
ADDITIONAL DISCLAIMER section of `LICENSE` for the full statement.

## Hardening notes for adopters

- The hook guards in `hooks/` are **opt-in**. Installing the plugin does not
  activate them; you wire them yourself in `.claude/settings.json`. See
  `hooks/README.md` for the wiring and the rationale.
- The guards are intentionally aggressive: they are designed so a false stop
  costs seconds and a missed leak does not happen. Read `hooks/README.md` before
  enabling them so the trade-off is a choice rather than a surprise.
- `hooks/pii-denylist.txt` ships with no active terms. If you add terms that are
  themselves sensitive, keep the file gitignored — `.gitignore` carries a
  commented line for this.
- **Working on this repository with the git-side shims enabled**: two tracked
  files trip the guards by construction —
  `test-corpus/cases/sec-hardcoded-secret/edge-01-aws-example-key.py` and
  `scripts/test_hooks.mjs`. The pre-commit shim only scans **added** lines, so
  they are only an obstacle in a commit that touches them; when that happens,
  `git commit --no-verify` is the documented escape, and the reason belongs in
  the commit message. Do not weaken the guard patterns to accommodate the tests —
  narrowing a detector so its own test stops firing is precisely the
  fix-without-fix failure (AB-2).
