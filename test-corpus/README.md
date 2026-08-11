# test-corpus - labeled synthetic corpus for measuring precision AND recall

**Status:** v0.2. **Full branch coverage - all 27 of 27** (23 original + 4
promoted supply-chain branches). 112 labeled cases, **symmetric per branch**
(every branch carries at least one TP / FP / FN / TN), split across two harnesses,
both green:

- **72 cases / 17 regex branches** -> `python test-corpus/score.py`
- **40 cases / 10 structural branches** -> `python test-corpus/structural/score_structural.py`

The first documented blind spot (`docker://...:latest`, an FN-A under
`supply-actions-floating-tag`) is now **caught** under `supply-unpinned-base-image`
(`tp-02-docker-latest`) - the corpus's designed promotion realized: the recall
ceiling (`verify_score.py`) rose 0.482 -> 0.491 because the skill grew reach.

This fulfills the Control-phase requirement ("the baseline target should be a
synthetic test corpus with labeled known-findings") and the branch re-entry rule
("the PR adding a branch includes a labeled test case in `test-corpus/`"). That
rule is no longer honour-system: `scripts/check_branch_schema.py` fails CI if any
branch in `trust-tree.yaml` has no labeled case. See `manifest.yaml` `coverage:`
and `structural/manifest.yaml`.

---

## Why this corpus exists - the recall gap

The skill's two real-codebase baseline runs measured
**precision** (83% then 100% - of the findings surfaced, how many were real).
It could **not** measure **recall** - of the real issues actually present, how
many the skill caught - because the ground truth on a real codebase is unknown.
Recall sat at "Pending / needs a second-opinion senior review" across both runs.

That asymmetry is dangerous in a Trust & Safety context, and naming it is the
whole point of this corpus:

> **A false positive wastes operator time. A false negative ships a live
> vulnerability the audit explicitly said nothing about.** The cost is not
> symmetric. An audit tool that optimizes only for precision is optimizing for
> the *cheaper* failure mode.

A synthetic corpus has **known ground truth by construction** - we plant the
vulnerabilities, so we know exactly what a perfect run would find. That makes
both metrics computable:

- **Precision** = TP / (TP + FP) - of what the skill flagged, how much was real.
- **Recall** = TP / (TP + FN) - of what was really there, how much the skill caught.

---

## The precision/recall tradeoff - stated explicitly

The skill's **two-signal prefilter** (`SKILL.md` § Phase 2) is, by construction,
a **precision-favoring design**. It drops every candidate finding that cannot
obtain an *independent, authoritative, falsifiable* second signal cheaply,
in-session. On Codebase A it dropped ~77% of raw candidates; on Codebase B, 50%.
That drop rate is exactly what produces the high precision numbers.

**Every one of those drops is a recall bet.** A candidate dropped because its
second signal was hard to obtain in-session is a candidate that - if it was a
*real* issue whose confirmation simply lived outside the prefilter's reach -
becomes a **false negative**. The prefilter cannot tell "false positive correctly
dropped" from "true positive wrongly dropped" without ground truth. This corpus
*is* that ground truth.

Reporting precision without recall is itself a form of the **survivorship bias**
the skill already warns against (`references/anti-behaviors.md` § AB-3): *"we
found few false positives"* is not *"we caught the real issues."* The corpus
therefore measures both, and weights the score toward recall (see Scoring).

This is not a flaw to be hidden - it is a **calibrated design choice that must be
documented so adopters know the edge of the audit.** The classes of true issue
the prefilter knowingly trades away are enumerated below.

---

## The false-negative taxonomy (the recall blind spots)

Five classes of false negative arise from the skill's architecture. The corpus
plants cases for the classes it *can* exercise (chiefly FN-B); the classes it
cannot exercise in code (FN-C/D/E are partly procedural) are named here so the
**recall budget** is explicit rather than silent.

| Class | Name | Where in the pipeline | Example |
|-------|------|-----------------------|---------|
| **FN-A** | Detection miss | Signal 1 never fires | A real SQLi via an ORM `raw()` call the `detect:` regex doesn't cover; a credential in a non-standard format; a file type outside `triggers:` (`.env.example`, shell scripts). Recall lost *before* the prefilter runs. |
| **FN-B** | Prefilter over-drop | Signal 2 wrongly clears a real Signal 1 | The confirming evidence is outside the verify window: cross-function taint the 20-line read can't trace; a sanitizer that *appears* present (so the prefilter drops as "safe") but is misconfigured/bypassable. **This is the class the corpus directly measures.** |
| **FN-C** | Deferred-and-forgotten | Signal 2 too expensive, never resolved | Confirmation needs a live request, a running app, or a tool not on PATH (`pip-audit`). Correctly deferred to the `AMBIGUOUS` queue - but a deferral that is never run is a silent recall hole. |
| **FN-D** | Out-of-scope-by-design | Category disabled / path pruned / surface unscanned | The real Codebase-B miss: a11y branches skipped because the scan was backend-only; the `apps/web` frontend never scanned. Ties to AB-3 (survivorship). |
| **FN-E** | Class-not-modeled | No branch exists for the vuln class | Timing attacks, race conditions / TOCTOU, business-logic flaws, deserialization, complex authz, SSRF-by-design in fetcher architectures (the Codebase-B "SSRF branch too narrow" observation). The unknown-unknowns the recall budget must name. |

**Contextual feature this taxonomy unlocks (suggested, not yet built):** every
audit report should carry a **`RECALL BUDGET:`** block - the FN-D and FN-E classes
the session could *not* cover ("we did not check: cross-file taint flows, timing
attacks, race conditions; the `web/` surface was out of scope"). That turns the
recall blind spot from an invisible gap into a declared edge, the same way the
`COVERAGE:` block (AB-3) turns absence-of-finding into declared coverage. See the
suggestion at the bottom of this file.

---

## Labeling schema

Ground truth lives in `manifest.yaml`, one entry per case. Case files stay small
and self-contained; the manifest is the machine-scorable source of truth.

```yaml
cases:
  - id: <branch-id>/<tp|fp|fn|tn|edge>-NN-<slug>
    branch: <branch-id from trust-tree.yaml>
    file: cases/<branch-id>/<filename>
    ground_truth: vulnerable | benign        # what is objectively true of the code
    expected_label: true_positive            # what a CORRECT skill run produces:
                                             #   true_positive  - detect fires, and it's real
                                             #   true_negative  - detect silent, and it's clean
                                             #   false_positive - detect fires on benign; verify MUST drop
                                             #   false_negative - real issue the skill is
                                             #                    EXPECTED to miss (documents
                                             #                    the recall cost, by class)
    expected_severity: CRITICAL | HIGH | MEDIUM | LOW | n/a
    second_signal_available: true | false    # can the prefilter confirm in-session?
    fn_class: FN-A | FN-B | FN-C | FN-D | FN-E | n/a
    edge_case: "optional - present when the case probes a specific detect/verify
                param boundary (the value names which boundary)"
    notes: "one line: why this case has this label"
```

**Fixtures carry NO rationale.** Each case file is a neutral header + the bare
specimen. *All* explanation lives here in the manifest - because the detection
harness scans the fixture, and a comment that quotes a trigger word (`probably`,
`<img`, `hashlib.md5(`) would make the fixture flag *itself*. (This is not
hypothetical: the first cut of these fixtures did exactly that, and `score.py`
caught it - see the `false_positive`-vs-`true_negative` distinction below.)

**`false_positive` vs `true_negative` is decided by the regex, not by hand.** An
FP is benign code the detect regex *fires* on (so verify must do the work of
dropping it); a TN is benign code the regex *correctly stays silent* on. If you
label something `false_positive` but the regex never fires, it is really a `true_negative`
- the detector's own specificity already handled it. `score.py` enforces this.

Note the deliberate distinction: `ground_truth` is about the **code**;
`expected_label` is about the **skill's correct behavior on that code**. A planted
vulnerability whose `expected_label` is `false_negative` is the corpus *honestly
encoding a known limitation* - running the skill and getting a miss there is a
**pass**, not a failure, because the corpus predicted it. Recall improves in a
future version when an `fn-*` case can be *promoted* to `expected_label:
true_positive` (i.e., the skill grew the reach to catch it).

---

## Scoring

A run over the corpus produces a confusion matrix per branch and overall:

```
precision = TP / (TP + FP)
recall    = TP / (TP + FN)        ← the metric the baseline runs could not compute
F_beta    = (1 + b^2) * (precision * recall) / (b^2 * precision + recall)
```

**Use F2 (β=2), not F1.** F2 weights recall twice as heavily as precision -
the correct asymmetry for a Trust & Safety tool where a false negative (a shipped
vulnerability) is the costlier error. Reporting F1 would silently re-balance the
tool back toward the cheaper failure mode the prefilter already favors.

The corpus also reports the **promotable-FN count**: of the `false_negative`
cases, how many a candidate change would convert to `true_positive`. That number
is the concrete v0.x -> v0.(x+1) recall-improvement target.

### What `score.py` does today (and doesn't)

`score.py` is the **detection-layer harness**. It pulls each branch's `detect:`
regexes from `trust-tree.yaml`, runs them against every fixture, and reports the
detection-layer confusion matrix (precision / recall / specificity) plus a
per-branch class-balance table. Critically, it **enforces label consistency**: a
`true_positive`/`false_positive`/`FN-B` case must trip detection; a
`true_negative`/`FN-A` case must not. A mismatch means the label or the fixture
is wrong. Run it after any corpus change: `python test-corpus/score.py` (exit 0 =
all consistent).

It scores the **regex pass only** - it cannot run the *verify* step (that needs a
human/LLM second signal). The full pipeline is scored by `verify_score.py`.

### What `verify_score.py` does (the verify layer)

`verify_score.py` scores the **full pipeline** (detect THEN verify), where the
unit of truth is *"did the skill SURFACE a finding?"* - what an operator actually
experiences. Two modes:

- **Designed mode** (`python test-corpus/verify_score.py`) - computes the corpus's
  *intended* metrics from the labels alone. A correct skill surfaces a finding
  only for `true_positive` cases (FP-bait is dropped at verify, TN never detects,
  FN is the known miss), so designed precision is **1.0 by construction** and
  designed **recall = TP/(TP+FN)** is the corpus's recall ceiling. It prints the
  **promotable-FN headroom** broken down by `fn_class` (FN-A reach gaps vs FN-B
  verify over-drops) and by branch - the concrete recall-improvement target.
- **Actual mode** (`python test-corpus/verify_score.py runs/<log>.yaml`) - a run
  log records `surfaced: true|false` per case from a real skill run. The scorer
  computes the observed confusion AND **diffs it against the design**: which
  `false_positive` cases *leaked* (verify failed to drop -> precision cost), which
  `false_negative` cases were *caught* (recall promotions - update the label),
  which `true_positive` cases were *missed* (regression). That gap is the verify
  step's report card, which the detection harness cannot see. See
  `runs/sample-run.yaml` for the run-log format (a synthetic illustrative log).

### Class balance & base rates

The corpus is **balanced per branch**: every branch carries at least one TP, FP,
FN, and TN. This is deliberate - each branch is a separate detector, so precision
= TP/(TP+FP) and recall = TP/(TP+FN) are computed *per branch*, and a branch needs
all four cells to be measurable. Balance also keeps the aggregate F2 from being an
artifact of class mix.

**Caveat (do not skip):** a balanced corpus is an *estimation tool*, not a mirror
of deployment. Real codebases are overwhelmingly TN-dominant - most code is clean.
So a balanced F2 measures *class-conditional* detector quality ("does it catch
issues and leave clean code alone"), **not** a deployment hit-rate. Read the
number as "how good is the detector per class," never as "this is what you'll see
in the wild."

---

## Directory layout

```
test-corpus/
  README.md                         this file - design, tradeoff, FN taxonomy, scoring
  manifest.yaml                     labeled index - the machine-scorable ground truth
  score.py                          detection-layer harness (regex branches; run after any change)
  verify_score.py                   full-pipeline scorer (designed metrics + run-log actual/gap)
  runs/sample-run.yaml              synthetic illustrative run log (verify_score.py actual mode)
  cases/
    <branch-id>/
      tp-NN-<slug>.<ext>            planted true positive    (detect fires; real)
      fp-NN-<slug>.<ext>            false-positive bait       (detect fires; verify drops)
      tn-NN-<slug>.<ext>            true negative             (detect correctly silent; clean)
      fn-NN-<slug>.<ext>            recall blind spot         (real issue skill is EXPECTED
                                    to miss - the WHY lives in the manifest)
      edge-NN-<slug>.<ext>          boundary case probing an exact detect/verify param
  structural/                       parallel corpus for STRUCTURAL / tool-call branches
    README.md                       the mini-repo pattern + how to extend
    manifest.yaml                   mini-repo ground truth
    score_structural.py             predicate harness (repo-shape detection, not regex)
    cases/<branch-id>/<label>-NN/   mini-repo fixtures (a directory tree, not one file)
```

Each fixture is a **neutral header + the bare specimen** - no rationale, no
trigger words in comments (so a fixture can't flag itself). The rationale lives in
`manifest.yaml`.

**Safety note:** secret-detection cases (`sec-hardcoded-secret`) use obviously
fake, structurally-shaped placeholders only - never a real or real-looking
credential. The corpus must never become a leak surface for the thing it detects.

---

## How a v0.2 baseline run uses this corpus

Per the DMAIC Control phase, **every v0.x release runs the corpus and records
precision, recall, and F2**. The numbers must improve or hold; a recall
regression blocks the release the same way a precision regression does. This
closes the loop the two real-codebase baselines left open: those measured
precision on unknown ground truth; this measures both on known ground truth.

---

## Suggested fast-follows

1. **`RECALL BUDGET:` report block** - **Built.** Now a required audit-report
   section (sibling to `COVERAGE:`) declaring the FN-D/FN-E classes a session
   could not cover. See `SKILL.md` + `references/dialogue-protocol.md`.
2. **Full-pipeline scoring** - **Built.** `score.py` (detection layer) +
   `verify_score.py` (verify layer: designed precision/recall/F2 + promotable-FN
   headroom, plus actual-vs-designed gap analysis from a captured run log).
3. **Per-branch recall targets in `trust-tree.yaml`** - an optional
   `known_fn_classes: [FN-B, FN-E]` field per branch, so each branch declares its
   own blind spots. (An open postulate: what if every branch declared its own false-negative class?)
4. **Structural / tool-call branch coverage** - **Built, all 9 of 9 covered.**
   `structural/` carries mini-repo fixtures + a predicate harness
   (`score_structural.py`) for every repo-shape branch - including the SPDX
   substring check (`license-dep-conflict`), WCAG contrast math
   (`a11y-color-contrast`), and the captured-`npm audit` tool-call
   (`supply-known-cve-deps`). See `structural/README.md`.
