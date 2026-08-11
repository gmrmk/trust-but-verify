# structural/ - corpus for structural & tool-call branches

The regex corpus (`../`) validates branches whose `detect:` is a single-file
**regex**. Some branches detect on **repo shape** instead - a missing lockfile, an
absent `SECURITY.md`, an un-attributed vendored dependency - or via a **tool call**
(`npm audit`). A regex over one file can't express those, so they live here with a
different fixture shape and a different harness.

## The shape

- A fixture is a **mini-repo directory**, not a single file:
  `cases/<branch-id>/<label>-NN-<slug>/` containing a small tree of real files.
- "Detection" is a **Python predicate** over that directory, registered in
  `score_structural.py` (`PREDICATES[branch_id]`), returning `True` if the
  structural problem is present.
- `manifest.yaml` labels each mini-repo (`expected_label`, `fn_class`, `notes`)
  exactly like the regex corpus.
- `score_structural.py` runs each predicate and enforces the **same
  label-consistency invariants**: `true_positive` / `false_positive` / `FN-B` must
  fire; `true_negative` / `FN-A` must stay silent. Run it after any change:
  `python test-corpus/structural/score_structural.py` (exit 0 = consistent).

## All 9 structural branches (each TP/FP/FN/TN, harness-validated)

| Branch | Predicate fires when... | The instructive edge cases |
|---|---|---|
| `supply-lockfile-missing` | a manifest is committed but no lockfile is | FP: a zero-dependency stub manifest (nothing to pin) · FN-A: a `Gemfile` (manifest type the predicate's map omits) |
| `op-missing-security-md` | no `SECURITY.md` at root or `.github/` | FP: a policy at `docs/security.md` (alternate location) · FN-A: an **empty** `SECURITY.md` (presence-only check can't see it's a stub) |
| `license-missing-attribution` | a vendored `LICENSE` exists but no root `NOTICE`/`CREDITS` | FP: a **CC0** vendored license (no attribution required; predicate can't read the type) · FN-A: an MIT asset under `src/embedded/` (outside the scanned `vendor/`) |
| `license-dep-conflict` | a dep license contains GPL/AGPL while the project is permissive (naive substring) | FP: a dual `(MIT OR GPL-3.0)` dep (substring fires; MIT can be chosen) · FN-A: a GPL dep whose license is only in a `LICENSE` file, not the manifest field |
| `a11y-color-contrast` | a CSS rule's fg/bg **hex** pair computes below WCAG AA 4.5:1 | FP: `#888` on `#fff` (~3.4:1) on **large text**, where 3:1 applies · FN-A: a low-contrast pair written with `rgb()` (no hex to parse) |
| `supply-known-cve-deps` | captured `npm audit --json` reports ≥1 vulnerability | FP: a report with **only low/info** advisories (below the actionable CVSS bar) · FN-A: a known-bad **vendored bundle** the tool never scans |
| `priv-no-data-rights` | the app references user PII but exposes no deletion/export route | FP: `user-agent` **telemetry** (matches the PII heuristic; stores no PII) · FN-A: a `/delete-account` route that is a **501 stub** |
| `priv-pii-plaintext` | a schema declares a PII column with a plaintext type and no encryption marker | FP: a `phone_model` **product** column (matches `phone`; not PII) · FN-A: PII nested inside a `JSONB` blob the column scan can't see |
| `op-no-rate-limit` | an auth route file defines login/signup with no rate-limit middleware in-file | FP: a **global** limiter in `app.js` (predicate scans only the route file) · FN-A: auth via `POST /api/session` (login by a name the keyword set omits) |

Each edge case exists to show the same lesson the regex corpus teaches: the
structural check is necessarily imprecise, and the corpus makes that imprecision
**measurable** - every FP is the predicate over-firing, every FN-A is a structural
blind spot named on purpose.

## Predicate fidelity - a deliberate caveat

These predicates are **corpus-grade**, not the skill's production detection. They
are intentionally simple (substring license checks, hex-only contrast parsing,
in-file route scans) so their blind spots are *legible* and each FN-A documents a
real, nameable gap. The skill's live structural detection can be richer; the
corpus exists to measure where a check's reach ends, not to be the check.

Two notes on fidelity:

- **`supply-known-cve-deps` is a captured tool-call.** The live branch runs
  `npm audit` / `pip-audit` / `cargo audit` (network + advisory DB -> non-deterministic).
  The corpus pins a captured `audit-report.json` per mini-repo so the harness is
  offline and reproducible. A live runner would gate on tool availability on PATH.
- **The FP/FN-A split is the point.** Every FP is a predicate over-firing on
  benign structure; every FN-A is a structural reach limit named on purpose. That
  is exactly the recall cost this corpus was built to make measurable.

## Adding a brand-new structural branch

Add a predicate to `PREDICATES` (keyed by the `trust-tree.yaml` branch id), drop
mini-repos under `cases/<branch-id>/<label>-NN-<slug>/`, add manifest entries with
`expected_label` + `fn_class`, and re-run `score_structural.py` until green.
