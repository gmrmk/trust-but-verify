# Root Cause Analysis Frameworks

Trust-but-verify surfaces a *symptom* (a load-bearing claim with no second signal). Before proposing a fix, the skill applies the RCA framework that best fits the finding's shape. This file is the selection guide.

The discipline:

> A fix that addresses the symptom without addressing the root cause is itself a load-bearing claim. Apply RCA before recommending a fix - or apply it openly with the operator at the dialogue step.

---

## Selection matrix

| Finding shape | Use | Why |
|---|---|---|
| Single clear symptom, causation chain unclear | **5 Whys** | Cheapest. One conversation, five questions, named root |
| Many candidate causes across people / process / tools / data | **Fishbone (Ishikawa)** | Categorical decomposition; surfaces the cause-class, not just the cause |
| Safety-critical; need to enumerate AND/OR threat paths | **Fault Tree Analysis (FTA)** | Deductive, top-down; rigorous for CRITICAL findings |
| Has upstream causes AND downstream consequences with barriers | **Bow-Tie Analysis** | Pairs naturally with blast-radius framing |
| Partial / intermittent / diagnostic - "what is and isn't happening" | **Kepner-Tregoe Problem Analysis** | Contrast-based; isolates distinguishing factors |
| Many findings in the same class, need to prioritize | **Pareto (80/20)** | Surfaces the few classes responsible for most findings |
| Process-level pattern (not a single finding) | **DMAIC** | Already in operator's doctrine; reference, don't duplicate |

The skill picks a default per branch in `trust-tree.yaml`; the operator can override at dialogue time.

---

## 5 Whys (Sakichi Toyoda · Toyota Production System)

**Best for:** single clear symptom, chain of causation unclear.

**Procedure:**

1. State the symptom in one sentence.
2. Ask "why does this happen?" - give the best-supported answer.
3. Apply rule of recursion: ask "why?" of that answer.
4. Repeat until you reach a cause that is actionable (you can fix it) AND systemic (fixing it prevents recurrence).
5. Five is a heuristic, not a quota. Stop at 3 if you arrive; continue past 5 if you haven't.

**Worked example (LICENSE placeholder finding from a baseline run):**

> **Symptom:** LICENSE file contains a 75-byte placeholder, not the Apache-2.0 text.
> **Why 1:** Why is the LICENSE a placeholder? - Because `pyproject.toml` references a deferred ADR for license selection and the decision was never propagated.
> **Why 2:** Why was the decision deferred? - Because the manufacturing plan flagged it as "pending §2.2 #1 confirmation" before launch.
> **Why 3:** Why hasn't the confirmation propagated to the file? - Because there's no automation linking the manufacturing-plan resolution to the on-disk LICENSE file.
> **Why 4:** Why no automation? - Because the project assumed a human would update the file when the decision landed.
> **Why 5:** Why didn't the human update it? - Because no checklist or pre-release gate references the LICENSE file specifically.
>
> **Root cause:** No pre-release gate validates that `pyproject.toml`'s declared license matches the on-disk LICENSE file content.
> **Fix at root:** Add a CI check (`tools/ci/license_consistency_lint.py`) that fails if the declared SPDX ID has no matching canonical text in LICENSE.
> **Fix at symptom (this finding's scope):** Replace LICENSE with canonical text. (Done.)

**Failure modes:**
- Stopping at "human didn't do it" - that's *blame*, not *cause*. Keep going until you reach a process or system gap.
- Branching uncontrolled - 5 Whys is linear by design. If multiple causes appear, switch to Fishbone.

**Authoritative reference:** [Toyota - Toyota Production System (TPS) overview](https://global.toyota/en/company/vision-and-philosophy/production-system/)

---

## Fishbone / Ishikawa Diagram (Kaoru Ishikawa · 1968)

**Best for:** many candidate causes across distinct categories.

**Procedure:**

1. State the effect (the symptom) as the "head" of the fish.
2. Draw the spine and attach 4-6 bone categories. Standard categories for code-domain trust-but-verify:
   - **People** - operator habits, knowledge gaps, team conventions
   - **Process** - workflow gaps, review/release gates, deploy pipelines
   - **Tools** - linters, type checkers, CI configuration
   - **Data** - fixtures, sample data, secrets handling
   - **Governance** - ADRs, policies, ownership boundaries
   - **External** - third-party deps, vendor APIs, regulations
3. For each category, brainstorm candidate causes. Quantity first, quality later.
4. Mark the candidates that survive a two-signal check.
5. The surviving candidates are the real cause-set; the symptom is the effect of their intersection.

**Worked example (floating GitHub Action tags finding from a baseline run):**

```
                                     People                Process
                                       |                      |
                     no maintainer aware of pinning       no PR template asking
                                       |                      |
                                       \______________________/_______
                                                                      \
                                                                       Effect:
                                                                       Actions
                                                                       pinned to
                                                                       floating tags
                                                                       (CI supply
                                                                       chain weak)
                                       _______________________________/
                                      /                       \
                                       |                       |
                  no SHA-pin linter configured            upstream docs use @v4
                                       |                       |
                                     Tools                  External
```

**Root-cause cluster:** No process step references SHA-pinning + no tool enforces it + upstream docs model the unsafe pattern. Fix any one of the three to mitigate; fixing all three is defense-in-depth.

**Failure modes:**
- Listing causes you already have a fix for - Fishbone is exploratory, not confirmatory.
- Skipping categories that "don't apply" - usually the empty category is where the surprise lives.

**Authoritative reference:** Ishikawa, K. *Guide to Quality Control* (Asian Productivity Organization, 1968). Modern overview: [ASQ - Fishbone Diagram](https://asq.org/quality-resources/fishbone)

---

## Fault Tree Analysis (FTA · US Military Standard 1629A / IEC 61025)

**Best for:** CRITICAL findings where you need to enumerate the conjunction (AND) and disjunction (OR) of conditions that produce the failure.

**Procedure:**

1. Define the **top event** - the failure you want to prevent (e.g., "investigator identity leaked").
2. Decompose downward: what immediate conditions produce the top event? Connect with AND gates (all required) or OR gates (any sufficient).
3. Recurse until each leaf is a **basic event** - an atomic, independently-probable cause.
4. Identify **minimal cut sets** - the smallest combinations of basic events that produce the top event.
5. Mitigation priority = cut sets with fewest basic events (cheapest to break).

**Worked sketch (top event: "user identity leaked via OPSEC failure" - illustrative for any privacy-sensitive tool):**

```
                          TOP: Investigator identity leaked
                                       |
                                      OR
                          ____________|____________
                         /             |            \
                  Log persistence    Network         Storage at
                  leak               fingerprint     rest leak
                       |              leak              |
                      AND             AND              AND
                      ...             ...              ...
```

This is the level where the skill stops and defers to a real threat-modeling exercise. **FTA is a 1-3-day exercise per top event, not a 5-minute dialogue step.** The skill cites FTA as the framework but recommends offline execution for any finding where the operator selects "do full FTA."

**Failure modes:**
- Treating FTA as exhaustive - basic events you didn't think of don't appear. FTA shines when paired with FMEA.
- Using FTA for non-safety-critical findings - overkill, costs operator hours that should go to coding.

**Authoritative reference:** [IEC 61025 - Fault tree analysis (FTA)](https://webstore.iec.ch/publication/4311) · [NASA Fault Tree Handbook (NUREG-0492)](https://ntrs.nasa.gov/citations/20000034348)

---

## Bow-Tie Analysis (Royal Dutch Shell · 1979)

**Best for:** findings with both **upstream causes** AND **downstream consequences**, where existing barriers may mitigate.

**Why it pairs with trust-but-verify:** the skill already computes "blast radius." Bow-tie makes the blast radius reasoning explicit - you map each consequence back to the controls between the top event and the downstream harm.

**Procedure:**

```
       Threats / causes              Top event                  Consequences
       ─────────────────             ─────────                  ────────────
         Cause 1 ──┐                                    ┌──── Consequence A
         Cause 2 ──┼──[ Preventive ]── Top event ──[ Mitigative ]── Consequence B
         Cause 3 ──┘    barriers                       barriers   └──── Consequence C
```

1. Center: state the **top event** (the loss of control - e.g., "API endpoint receives an unauthenticated request").
2. Left side: causes / threats that could produce the top event. Between each cause and the top event, identify **preventive barriers** (controls that stop the cause from producing the event).
3. Right side: consequences if the top event occurs. Between the top event and each consequence, identify **mitigative barriers** (controls that limit damage).
4. Assess: which barriers are real? Which are missing? Which are degraded?

**Worked example (no-API-auth finding from a baseline run):**

```
  Threats:                           Top event:                    Consequences:
  - Accidental ext. exposure         API endpoint receives          - Investigator identity
    (host config change)             unauthenticated request          inferred from queries
  - SSRF from worker                                                - Sock-account state
  - Local malware probing                                            mutated
                                                                    - Logless contract bypass
   Preventive barriers (real):      Mitigative barriers (real):
   - 127.0.0.1 bind by default       - Logless contract on access logs
   - single-user scope (declared)    - Row-level encryption (partial, per ADR)
   - local-only deployment           - Per-record signing (per ADR)

   Preventive barriers (missing):    Mitigative barriers (missing):
   - No middleware enforcement       - No rate limit on suspicious patterns
     of the bind                     - No alerting on unexpected origin
```

**Result:** Finding 7's "accept as trust-debt" is correctly placed *because* multiple preventive barriers exist (3 real) and multiple mitigative barriers exist (3 real). The decision is barrier-aware, not faith-based.

**Failure modes:**
- Listing barriers that don't actually function - phantom barrier is worse than no barrier.
- Skipping the mitigative side - once the top event happens, mitigative barriers are all you have.

**Authoritative reference:** [CGE Risk - The Bow-Tie Method](https://www.cgerisk.com/knowledgebase/The_bowtie_method) · ISO 31010:2019 Risk assessment techniques (§B.4.2)

---

## Kepner-Tregoe Problem Analysis (Kepner & Tregoe · 1965)

**Best for:** partial / intermittent / "it works sometimes" findings where the *contrast* matters more than any single cause.

**Procedure:** Build the IS / IS NOT matrix.

| Dimension | IS (where the problem appears) | IS NOT (where it does not) | Distinguishing factor |
|---|---|---|---|
| What | <symptom is observed> | <similar artifact where symptom is absent> | <what differs> |
| Where | <files / modules / hosts> | <where it doesn't appear> | <what differs> |
| When | <time / session / build> | <when it doesn't appear> | <what differs> |
| Extent | <how much / how often> | <bounded by what> | <what bounds it> |

The distinguishing factors are the candidate causes.

**Worked example (empty-architectural-package finding from a baseline run):**

A multi-package monorepo had a layered DAG declaration that reserved an L1 slot for an opsec/security-controls package, but the package contained only an `__init__.py`. The relevant primitives existed - they lived inline in an L4 application package.

| Dimension | IS | IS NOT | Distinguishing factor |
|---|---|---|---|
| What | The named L1 package is empty | Sibling L1 packages are implemented | The empty package lacks a primary consumer; the others have one |
| Where | The dedicated package directory | Inline code in an L4 application | Code exists, just not in the named package |
| When | Since the L1 layer was declared in the DAG | Before the layered DAG existed | DAG declared a slot before extraction was justified |
| Extent | Only the one package; not its siblings | All sibling L1 packages have at least one module | Architectural reservation outpaced implementation |

**Distinguishing factor synthesis:** The L1 slot was reserved by DAG design, but the actual primitives evolved inline in the consuming layer because there was only one consumer. Single-consumer pattern is the root.

**Result:** Confirms a signpost-fix disposition (point the README at the real locations until a second consumer justifies extraction).

**Authoritative reference:** Kepner, C. & Tregoe, B. *The Rational Manager* (McGraw-Hill, 1965). Modern overview: [Kepner-Tregoe - Problem Analysis](https://kepner-tregoe.com/problem-solving-methodology/)

---

## Pareto Analysis (Vilfredo Pareto · 1896 · 80-20 principle)

**Best for:** prioritizing across many findings - not for analyzing a single finding.

**Procedure:**

1. After Phase 2 scan, tally findings by `(category, branch_id)`.
2. Sort descending by count.
3. The top 20% of branches that produce 80% of findings are the priority targets for Phase 3 - they're systemic.
4. Findings in the long tail are isolated; address opportunistically.

**When the skill applies it:**

If Phase 2 surfaces 15+ findings, Phase 3 opens with a Pareto summary:

```
  Pareto-cluster (80% of findings come from 20% of branches):

    1. supply_chain/floating_tags        7 findings  (47%)
    2. license/missing_text              3 findings  (20%)
    3. operational/stub_documentation    2 findings  (13%)
    ─── 80% line ───
    4. security/auth_missing             1 finding   ( 7%)
    ...

  Suggestion: walk the top 3 branches together (12 findings as a cluster)
  before single-finding mode. Want to do that?

  [1] Walk clusters first
  [2] Walk in original sorted order
```

**Failure modes:**
- Treating 80/20 as a law - it's a heuristic; some codebases are flat. Use only when the distribution is actually skewed.

**Authoritative reference:** Juran, J. *Quality Control Handbook* (McGraw-Hill, 1951) - introduced Pareto principle to quality. Modern: [ASQ - Pareto Chart](https://asq.org/quality-resources/pareto)

---

## DMAIC (Six Sigma · Motorola 1986)

**Best for:** process-level patterns - not findings.

**Process-level framework.** Reference only, do not duplicate. The skill's relationship to DMAIC:

- **Define:** Phase 1 (scope + categories)
- **Measure:** Phase 2 (scan + prefilter)
- **Analyze:** Phase 3 (the dialogue + this file's RCA frameworks)
- **Improve:** Phase 3's apply-fix path
- **Control:** Phase 4 (capture + trust-debt ledger + re-review windows)

The skill *is* a DMAIC cycle for trust-and-safety claims.

**Authoritative reference:** [ASQ - DMAIC](https://asq.org/quality-resources/dmaic)

---

## Composability

These frameworks are not exclusive. A typical heavy finding uses two:

- **5 Whys then Fishbone** - start linear, switch when branches appear.
- **Fishbone then Pareto** - categorical brainstorm, then weight which category to fix.
- **Bow-Tie then Fault Tree** - high-level barrier map, then deep enumeration of one barrier.
- **Kepner-Tregoe then 5 Whys** - isolate the distinguishing factor, then drill into why it differs.

The skill picks a default per `trust-tree.yaml` branch. The operator can override at the dialogue step:

```
  Apply RCA framework before proposing a fix?

  [1] 5 Whys              (recommended for this branch)
  [2] Fishbone / Ishikawa (if many candidate causes)
  [3] Bow-Tie             (if blast radius is the question)
  [4] Skip - fix at symptom level only
```

---

## When NOT to apply RCA

- **TINY blast radius + LOW severity** - symptom-level fix is fine. RCA is overhead.
- **CRITICAL severity + clear cause already proven by two signals** - applying RCA delays the fix. Just fix it, then post-fix RCA if the pattern repeats.
- **Operator is in a flow state on unrelated work** - defer RCA to the audit-report capture phase.

The skill respects operator time. RCA is a tool, not a checklist item.

---

## How this integrates with the dialogue

The Four-Option Dialogue Protocol gains an optional fifth interaction in `references/dialogue-protocol.md`:

```
  Before I propose a fix, would you like me to apply a root-cause
  framework to this finding?

  [Recommended: 5 Whys - quick, one-conversation]
  [Or: Fishbone / Bow-Tie / Kepner-Tregoe / Skip - fix the symptom]
```

This appears between option-presentation and option-execution when the finding's severity is HIGH or CRITICAL, or when the operator selects "verify more" repeatedly on the same finding (signal that the cause isn't obvious).

---

## Sources consulted

- Toyota Production System overview (Toyota Global)
- Ishikawa, K. *Guide to Quality Control* (1968)
- ASQ - Fishbone / Pareto / DMAIC quality resources
- IEC 61025 - Fault tree analysis (FTA)
- NASA Fault Tree Handbook (NUREG-0492)
- CGE Risk - The Bow-Tie Method
- ISO 31010:2019 Risk assessment techniques
- Kepner & Tregoe, *The Rational Manager* (1965)
- Juran, *Quality Control Handbook* (1951)

100% of frameworks are real, named, and verifiable to a primary or authoritative secondary source. No fabricated frameworks in this list.
