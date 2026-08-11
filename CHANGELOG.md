# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Continuous integration.** `.github/workflows/ci.yml` runs the two detection
  harnesses, the full-pipeline scorer, the branch-schema gate, and the hook
  smoke tests on every push and pull request. Until now every "MUST" in
  `SKILL.md` was an instruction to a reader rather than a constraint on the
  artifact.
- **`scripts/check_branch_schema.py`** — mechanized branch-schema gate. Enforces
  what `trust-tree.yaml` and `SKILL.md` declare non-negotiable: grounding
  resolves to the framework registry, `verify:` is present and not a restatement
  of `detect:`, `last_verified:` is a real non-future date, liability templates
  carry the key pair their category requires, every `detect:` regex compiles,
  `rca_defaults:` covers exactly the branch set, every branch has at least one
  labeled corpus case, and the registry agrees with `references/grounding.md`.
- **`scripts/check_citations.py`** — citation-liveness gate (anti-AB-1), run
  weekly, on demand, and on every release tag via
  `.github/workflows/citations.yml`. Distinguishes a **gone** citation (404/410,
  a hard failure) from a **blocked** one (403/429 — the host refused the client,
  which proves nothing about the document). Deliberately not a pull-request gate:
  a transient outage at a standards host must not train anyone to click past a
  red check (AB-9).
- **`scripts/test_hooks.mjs`** — 25 hermetic smoke tests covering all four hook
  guards, including the AB-5 property that a guard never echoes the secret it
  caught.
- **`SECURITY.md`** — private vulnerability reporting, response expectations, and
  an explicit scope statement separating a guard bypass (in scope) from the
  deliberately vulnerable corpus fixtures and from detection precision/recall
  bugs (both out of scope).
- **Plugin packaging.** `.claude-plugin/plugin.json` and
  `.claude-plugin/marketplace.json` make the skill installable with
  `/plugin marketplace add gmrmk/trust-but-verify` instead of a manual
  `git clone && cp -r`.
- **`requirements.txt`** — the harnesses have always needed PyYAML and never
  declared it, so a fresh clone failed on import. Pinned exactly, because the
  repo's own `supply-floating-version-range` branch treats a floating range as a
  finding.
- `tbv-uncertainty-protocol` registered in `baseline_frameworks:` with
  `external: false`, so the three epistemic branches cite a registry id like
  every other branch. The schema gate permits in-repo grounding **only** for
  epistemic branches — a security or privacy branch can never ground itself in
  this repo's own prose.

### Fixed

- **`closure-claim-guard.mjs` never blocked `100%`.** The pattern was
  `\b(100%|…)\b`; a word boundary after `%` requires a word character next, so
  `100% clean` never matched despite `hooks/README.md` advertising it. Found by
  the new smoke tests. `100\s*%` is now its own alternative, and the case is
  covered so it cannot regress.
- `supply-known-cve-deps` was missing `user_harm` and `op-missing-security-md`
  was missing `legal_exposure` from their liability templates, both of which
  `SKILL.md` requires. Filled in; the schema gate now enforces the pair.
- The repository failed its own `op-missing-security-md` branch (no
  `SECURITY.md`). It no longer does.

### Changed

- **Repository restructured into a plugin layout.** The skill moved to
  `skills/trust-but-verify/` and the corpus moved out of the skill directory to
  `test-corpus/` at the repo root. Installing the skill previously copied 112
  fixtures — including deliberately vulnerable code and secret-shaped
  placeholders — into `~/.claude/skills/`. The runtime payload is now
  `SKILL.md`, `trust-tree.yaml`, and `references/` only.
- `test-corpus/score.py` resolves `trust-tree.yaml` explicitly and fails with a
  clear message if it is missing, rather than assuming its parent directory is
  the skill root.
- Documentation corrected against the artifact: `README.md` documented one of
  four hook guards; `SKILL.md` said verification "can be subverted in twelve
  known ways" while `references/anti-behaviors.md` catalogues seventeen; the
  six-category table omitted the `epistemic` category that owns three branches;
  and three files referenced a roadmap document that is not in the repository.

## [0.2.0]

### Added

- Four v0.2 supply-chain branches: `supply-floating-version-range`,
  `supply-install-scripts`, `supply-unpinned-base-image`,
  `supply-actions-excessive-permissions`.
- `test-corpus/structural/` — mini-repo fixtures and a predicate harness for the
  ten structural / tool-call branches.
- `test-corpus/verify_score.py` — full-pipeline scorer with designed-mode
  metrics, promotable-FN headroom, and actual-vs-designed gap analysis.
- Four hook guards (`pii-guard`, `secret-scan-guard`, `closure-claim-guard`,
  `irreversible-op-guard`) plus git-side shims.

### Changed

- Corpus reached full branch coverage: 112 labeled cases across all 27 branches,
  symmetric per branch (each carries at least one TP / FP / FN / TN).
- The first documented blind spot (`docker://…:latest`, an FN-A under
  `supply-actions-floating-tag`) was promoted to a true positive under
  `supply-unpinned-base-image`, raising the designed recall ceiling from 0.482
  to 0.491.

## [0.1.0]

- Initial skill: four phases, the two-signal verification gate, the four-option
  dialogue protocol, the anti-behavior catalogue, and 23 branches across six
  trust-and-safety categories plus the epistemic category.
