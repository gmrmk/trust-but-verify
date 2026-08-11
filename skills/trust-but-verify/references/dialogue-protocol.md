# Dialogue Protocol - the Four-Option Pattern

This is the conversational interface of the skill. Every finding surfaced in Phase 3 is presented using this exact structure.

> **Four options.** Reframe and Tell-me-more are possible future additions.

## Visual discipline - non-negotiable

**The skill is a polished interactive experience, not a wall of text.** Two rules are mandatory:

1. **Every finding opens with a printed banner** (markdown, in the assistant's response). The banner format below is the only acceptable form. Do not omit the rule lines. Do not omit the severity icon. Do not collapse onto one line.

2. **The four options are presented via the `AskUserQuestion` tool**, not as a numbered list in the chat text. The chat text contains the finding body; the `AskUserQuestion` call renders the dispositions as **selectable option chips**.

   **What the operator actually sees (important for adopters):** Claude Code has **no clickable UI overlay or "popup."** `AskUserQuestion` presents a compact set of **labeled option chips** the operator selects, with an automatic "Other" affordance for free-text. Earlier drafts of this skill called these "clickable popups" - that was a misnomer. The correct mental model is **option chips**, not a modal window. *Every* operator choice-point in this skill - dispositions, bypass confirmations, the RCA selector, Phase-1 setup, the trust-debt re-review window - uses these chips, never a typed `1`/`2`/`3`/`4` menu. Printing options as text and waiting for typed input is the deprecated v0.0 MUD path. Never do that.

If `AskUserQuestion` is genuinely unavailable in the current environment (e.g., a subagent context without the tool), fall back to a printed numbered list - and announce the fallback in one line so the operator knows why.

## The header block

```
─────────────────────────────────────────────────────────────────────
FINDING <N> of <T>  ·  [severity] [category]  ·  Blast radius: [LARGE | MEDIUM | TINY]
─────────────────────────────────────────────────────────────────────
```

### Severity icons

| Symbol | Label | Meaning |
|--------|-------|---------|
|  | CRITICAL | Cannot ship without addressing. Direct user harm or legal exposure observable. |
|  | HIGH | Fix before release. Real failure mode demonstrated in this codebase or directly analogous. |
|  | MEDIUM | Quality issue masking real problems. Fix if convenient. |
|  | LOW | Style / convention nit. Surface but don't insist. |

**Severity never silently downgrades.** Operators can accept-as-trust-debt - that's explicit. The finding's underlying severity stays in the ledger.

### Blast radius

Computed by the skill from:
- File scope (user-facing / deployed / committed to public repo / in git history)
- Dependency reach (via grep, or any code-graph index the project provides)

| Label | Meaning |
|-------|---------|
| LARGE | Affects all users, or has reached external dependents, or is in production-deployed code |
| MEDIUM | Affects most users in some workflow, or committed to main but not deployed |
| TINY | Affects only the operator, or is in local scratch / draft |

## The findings body - required fields

Every finding presents these seven fields **in this order**:

```
  Claim being audited:
    "<the literal load-bearing assertion, quoted from the artifact>"

  Source:
    <file:line>

  Evidence that flagged this:
    <what the detection produced + what the two-signal prefilter concluded>

  Risk if wrong:
    <who/what is harmed, in what way, with what reversibility>

  Proposed verification:
    <the specific check, naming the official source it queries>

  Proposed fix (if verification confirms):
    <concrete repair recipe - diff-ready when possible>

  Authoritative grounding:
    <framework + section + URL>
```

The Authoritative grounding field is non-negotiable for trust-and-safety baseline findings.

## The Liability Framing block - required for T&S baseline categories

For categories: security, privacy, license, supply_chain, operational.

```
  LIABILITY FRAMING

  User harm:        <concrete, specific impact on real users>
  Legal exposure:   <named statute / regulation / standard violated,
                     with section numbers where applicable>

  [If applicable:]
  Required action:
    <action beyond the code change - e.g. "ROTATE THE CREDENTIAL
     AT THE PROVIDER", "FILE A BREACH NOTIFICATION", "ESCALATE TO COUNSEL">
```

For category 4 (accessibility), the framing changes to user-harm voice:

```
  ACCESSIBILITY IMPACT

  Users affected:
    <which assistive-tech / disability cohort cannot use the artifact>

  WCAG criterion violated:
    <e.g. WCAG 2.2 Level AA 1.4.3 Contrast (Minimum)>

  Legal context:
    <ADA Title III (US user-facing); Section 508 (US federal procurement)>
```

## The four options - always presented via AskUserQuestion

The chat text ends with one short framing sentence: "Which path?" (or equivalent). The four options themselves are presented through the `AskUserQuestion` tool, which renders as **selectable option chips** (not a typed list, and not a floating UI overlay - see Visual discipline rule 2 for the actual operator UX).

**Canonical AskUserQuestion payload for a Phase-3 finding:**

```json
{
  "questions": [{
    "question": "<one-sentence restatement of the finding + 'Which path?'>",
    "header": "Finding <N>",
    "multiSelect": false,
    "options": [
      {
        "label": "Run verification (Recommended)",
        "description": "<one sentence: what gets fetched/queried, what authoritative source, why this is the safe first step>"
      },
      {
        "label": "Apply fix",
        "description": "<one sentence: the concrete change + estimated time + any side effects>"
      },
      {
        "label": "Accept as trust-debt",
        "description": "<one sentence: what gets logged + the re-evaluation trigger>"
      },
      {
        "label": "Skip silently",
        "description": "Defer entirely. No documentation, no fix. Re-surfaces at next baseline."
      }
    ]
  }]
}
```

**Rules for AskUserQuestion payloads in this skill:**

- `header` is always `"Finding <N>"`. Max 12 chars per the tool's constraint.
- `multiSelect` is always `false` for the four-option dialogue.
- The recommended option (per the skill's branch defaults) is listed FIRST with `" (Recommended)"` suffixed to its label.
- Each `description` is exactly one sentence and carries the trade-off, not the mechanics.
- The order of the remaining three options MUST reflect cost/effort ascending OR most-likely-secondary-choice, whichever surfaces the real decision more clearly. Ordering is operator-facing UX, not arbitrary.
- Never include "Other" as a manual option - the tool adds it automatically.

**The conceptual four options remain unchanged. The default and recommended option is ALWAYS verification:**

| Option | Behavior | Discipline status |
|---|---|---|
| **Run verification** | Fetch / query / execute the second-signal check | Satisfies the discipline. Default. |
| Apply fix | Skip verification, apply the proposed change |  BYPASS. Triggers mandatory bypass confirmation; recorded as `verification_bypassed: true` in the audit report. HIGH/CRITICAL findings require a second re-confirmation. |
| Accept as trust-debt | Log to ledger with re-review window | Discipline-compatible (the finding is acknowledged, not silently dismissed). Re-review re-runs verification. |
| Skip silently | Suppress; never surface again |  Permanent. Use only when the finding is genuinely N/A for this codebase. NOT a way to escape verification. |

**Default ordering:** Recommended-first, with verification options on top. For HIGH/CRITICAL findings, "Apply fix" is renamed `"Apply fix (VERIFICATION BYPASS)"` and moved below "Accept as trust-debt" so the bypass is visually de-emphasized.

## Optional RCA interstitial (HIGH / CRITICAL findings only)

Before option-execution, for HIGH or CRITICAL findings - OR when the operator picks "Run verification" twice on the same finding (signal that the cause isn't obvious) - the skill offers an RCA framework selection.

**This is a second AskUserQuestion call, not a printed list.** Payload:

```json
{
  "questions": [{
    "question": "Before proposing a fix, apply a root-cause framework to this finding?",
    "header": "RCA framework",
    "multiSelect": false,
    "options": [
      {"label": "5 Whys (Recommended)", "description": "Linear interrogation, one conversation. Fastest. Best when symptom is clear and chain is unclear."},
      {"label": "Fishbone (Ishikawa)", "description": "Categorical decomposition across People / Process / Tools / Data / Governance / External. Best when many candidate causes exist."},
      {"label": "Bow-Tie", "description": "Map upstream causes + downstream consequences with existing barriers. Pairs with blast-radius framing."},
      {"label": "Skip RCA - fix at symptom level", "description": "Apply the proposed fix without root-cause analysis. Re-surfaces if pattern repeats."}
    ]
  }]
}
```

Full framework descriptions and selection matrix: `references/rca-frameworks.md`.

After RCA selection, the skill walks the chosen framework in the chat (5 Whys conversationally, Fishbone as a categorized list, Bow-Tie as a labeled diagram). Then it returns to the four-option dialogue with the root-cause-informed fix.

**For TINY-blast-radius LOW findings, skip the RCA interstitial entirely.** Don't burn operator time on overhead disproportionate to the finding.

### Option [1] - Run the verification (the discipline path)

**This is the default and recommended path for every finding.** It is the only path that satisfies the skill's discipline. Selecting it means the operator is letting the second signal decide the framing - the verification result is authoritative, even when it contradicts the initial finding (especially then).

The verification check is the literal `verify:` field from the branch in `trust-tree.yaml`. It MUST satisfy the three properties - *independent, authoritative, falsifiable* - defined in `SKILL.md` § *"What verification MUST be."* If a branch's `verify:` field does not satisfy these, the branch is broken and MUST be fixed before findings ship from it.

**Auto mode:** Verification executes immediately. The result is shown verbatim - including the raw output, the source, and the resolution:

```
  -> Running: WebFetch https://anime.js.org/documentation/
  -> Source: anime.js official docs (canonical)
  -> Result: HTTP 200. Page content includes "anime() returns a Timeline".
  -> Signal 1 (detection): code imports `animejs/lib/anime.es.js` from CDN
  -> Signal 2 (this fetch): canonical docs confirm import path
  -> Outcome: VERIFIED - finding's framing is correct.

  -> AskUserQuestion chips: "Apply the fix" · "Show diff first" · "Cancel - back to dispositions"
```

If the verification REFUTES the finding:

```
  -> Result: HTTP 404 Not Found.
  -> Signal 1 (detection): code references CDN URL /lib/anime.min.js
  -> Signal 2 (this fetch): URL does not exist on CDN
  -> Outcome: VERIFIED REFUTATION - the URL is wrong.
            The framing of this finding changes from "potentially-wrong URL"
            to "confirmed-wrong URL." Severity raised from MEDIUM to HIGH.

  -> AskUserQuestion chips: "Apply the corrected fix" · "Show diff first" · "Cancel"
```

If the verification PARTIALLY refutes:

```
  -> Outcome: CONTRADICTION. Signal 1 framed this as <X>; Signal 2 reveals <Y>.
            Finding reframed below.
```

Then the skill restates the finding with the new framing and continues. **A contradiction is not a failure - it is the discipline working.**

**Ask-first mode:** The skill names the verification BEFORE executing and waits for explicit go-ahead:

```
  About to verify: WebFetch <URL> + Read 20 lines of context around <file:line>
  Source authority: <canonical URL of the framework/spec being checked against>
  Expected pass criterion: <what counts as "verified">
  Expected fail criterion: <what counts as "refuted">

  -> AskUserQuestion chips: "Proceed with verification" · "Change the verification" · "Skip - surface as AMBIGUOUS"
```

If the operator picks "skip and surface as AMBIGUOUS," the finding still enters the audit report - but labeled `AMBIGUOUS - verification declined`, with the would-have-checked recorded. This is honest; pretending the finding is verified when the operator skipped the check is not.

### Option [2] - Apply fix WITHOUT verification (BYPASS)

**This option bypasses the discipline of the skill.** The operator is explicitly choosing to act on a single-signal finding without obtaining the second signal. The skill enforces this with a mandatory bypass-confirmation flow.

#### Step 1 - Mandatory bypass confirmation (all severities)

A second `AskUserQuestion` fires before the diff is shown. It names *what verification would have checked*, so the operator is choosing to skip with full visibility:

```json
{
  "questions": [{
    "question": "Apply fix WITHOUT verification. The verification would have checked: <the specific second-signal check>. The outcome of that check would have determined whether the proposed fix is correct. Proceeding bypasses this gate. Confirm bypass?",
    "header": "Bypass verify",
    "multiSelect": false,
    "options": [
      {"label": "Run verification instead (Recommended)", "description": "Revert to Option 1. The verification takes <estimate> and produces a clean pass/fail."},
      {"label": "Confirm bypass - apply fix without second signal", "description": "Proceed without verification. The audit report will record `verification_bypassed: true` for this finding."},
      {"label": "Cancel - return to disposition menu", "description": "Go back to the four-option dispositions for this finding."}
    ]
  }]
}
```

#### Step 2 - HIGH / CRITICAL findings: second re-confirmation

For findings of severity HIGH or CRITICAL, a SECOND confirmation `AskUserQuestion` (option chips) fires after step 1, naming the user-harm and legal-exposure framing:

```json
{
  "questions": [{
    "question": "This finding is <SEVERITY>. User harm if the diagnosis is wrong: <user_harm>. Legal exposure if the diagnosis is wrong: <legal_exposure>. The bypass means the fix may not address the actual root cause. Still bypass?",
    "header": "HIGH/CRIT bypass",
    "multiSelect": false,
    "options": [
      {"label": "Run verification instead (Strongly Recommended)", "description": "Revert to Option 1 - verification is cheap relative to the consequence of a wrong fix at this severity."},
      {"label": "Confirm - I accept the risk of an unverified fix at this severity", "description": "Proceed. The audit report will flag this with `verification_bypassed: true` AND `bypass_on_high_severity: true`."}
    ]
  }]
}
```

#### Step 3 - Apply the diff

Only after the confirmation chain (step 1, and step 2 if applicable) does the skill show the diff and apply it:

```
  Applying fix to <file:line> (verification bypassed):

    - <old line>
    + <new line>

  -> AskUserQuestion chips: "Confirm - apply the diff" · "Show full file first" · "Cancel"
```

After confirmation: edit, read back to confirm it landed.

#### Step 4 - Post-fix re-verification (MANDATORY per AB-2)

Before moving to the next finding, the skill MUST run the branch's `post_fix_verify:` step on the changed file. This is the defense against fix-without-fix:

```
  Fix applied to <file:line>. Running post-fix verification:
    -> Branch <branch_id> requires: <post_fix_verify criterion>
    -> Result: <PASS | STILL_PRESENT | UNVERIFIABLE>
```

**If `post_fix_verify` PASSES:** the finding is recorded as `applied_and_verified: true`. Continue to next finding.

**If `post_fix_verify` returns `STILL_PRESENT`:** the finding is REOPENED. Record `applied_but_unverified: true`. Surface to operator:

```
   Fix applied but NOT verified.
  The recorded fix does NOT mitigate the vulnerability - it only edited
  the string that matched the detection regex. The vulnerability class
  is still present in the modified function.

  This finding has been REOPENED. How to proceed?
```

Then a new `AskUserQuestion` offers: re-attempt fix (Option [2] with the new context) · escalate to RCA (5 Whys to find why the symptom-fix didn't address the root) · accept as trust-debt with `unverified_fix_attempt: true` annotation · skip.

**If `post_fix_verify` cannot run (`UNVERIFIABLE`):** the fix is marked `unverifiable_in_session` and the operator MUST acknowledge before the session can complete Phase 4. The audit report flags `requires_human_re_review: true`.

For branches where `post_fix_verify` is marked `not_applicable: true` (vulnerability class requires runtime exercise, e.g., a CSRF token check that needs a live request), the audit report flags `human_re_review_required: true` instead.

#### Bypass recording

Every Option-[2] disposition writes the following to the session's audit report under the finding's outcome:

```yaml
disposition: applied
verification_bypassed: true
bypass_confirmed_at: <ISO timestamp>
bypass_on_high_severity: <bool>   # true if severity was HIGH or CRITICAL
would_have_verified: |
  <the verification step that was skipped, verbatim from the finding>
fix_applied: <file:line summary>
```

Phase 4 summary surfaces the bypass count separately:

```
Audit session complete.

Verified:                <N> of <M> findings via second-signal checks
Fixed with verification: <N>
Fixed via BYPASS:        <N>  ← surfaced separately, not hidden in "fixed"
Accepted as trust-debt:  <N>
Skipped silently:        <N>
```

**The bypass count is not a shame metric - it's a transparency metric.** Some bypasses are legitimate (operator has independent grounds to trust the diagnosis). But hiding bypasses in the "fixed" total would erode the discipline. Always surface separately.

### Option [3] - Accept as trust-debt

Two inputs - a free-text reason, then an `AskUserQuestion` for the window:

**1. The reason** is a genuine free-text response (a typed sentence or two is
correct here - this is open prose, not a choice menu, so it is *not* a MUD prompt):

```
  Accepting as trust-debt. Why is this acceptable for now?
  (1-3 sentences. Future-you and future-Claude will read this.)
  > <free text>
```

**2. The re-review window** is an `AskUserQuestion`. Note the tool's **4-option
cap**: the six conceptual windows don't all fit as chips, so the four most-common
are chips and the auto-added "Other" captures "Never (permanent)" and a specific
event trigger:

```json
{
  "questions": [{
    "question": "When should I re-surface this trust-debt finding?",
    "header": "Re-review",
    "multiSelect": false,
    "options": [
      {"label": "90 days (Recommended)", "description": "Re-surface in ~3 months - the default cadence for accepted debt."},
      {"label": "30 days", "description": "Re-surface in a month - for debt expected to clear soon."},
      {"label": "1 year", "description": "Re-surface in 12 months - for low-urgency, stable debt."},
      {"label": "On a specific event", "description": "Tie re-review to a trigger (next release, after migration X) - name it via Other."}
    ]
  }]
}
```

Via "Other," the operator can choose "Never (permanent acceptable debt)", a custom
duration (e.g., 180 days), or a specific event trigger.

Then write the entry to `<project>/docs/trust-debt-ledger.md`:

```yaml
- fix_id: TBD-<YYYY-MM-DD>-<slug>
  date_accepted: <YYYY-MM-DD>
  finding_class: <branch_id from trust-tree.yaml>
  severity: <severity>
  file: <file:line>
  claim: |
    <the quoted claim from the finding>
  reason: |
    <operator's free-text rationale>
  re_review: <date or 'never' or 'on:<event>'>
  audit_report: docs/audits/AUDIT-<date>-trust-but-verify.md
```

(The ledger is project-local. A user-wide ledger spanning projects is not
implemented.)

### Option [4] - Skip silently

Write suppression entry to `<project>/.trust-but-verify-suppress.yml`:

```yaml
# .trust-but-verify-suppress.yml
# Suppression rules for the trust-but-verify skill.
# Operators chose [4] Skip silently on these findings.
# Edit or remove entries to re-enable surfacing.
suppressions:
  - finding_class: <branch_id from trust-tree.yaml>
    file: <file:line that was skipped>
    suppressed_at: <ISO date>
    note: |
      <optional operator note - empty if not provided>
```

**Skip is NOT trust-debt.** Trust-debt is "I see it, choosing not to fix now, re-surface later." Skip is "this isn't a finding in this context, never surface again." Different intents, different storage.

If the skill returns to a finding that's in `.trust-but-verify-suppress.yml`, it's silently dropped in Phase 2 before reaching the operator.

## Phase 1 - full session-opening script

Each operator decision below is an `AskUserQuestion` (option chips), shown here in
linear form for readability - the `-> AskUserQuestion chips:` lines carry the actual
option labels, never a typed `1`/`2`/`3` menu.

```
─────────────────────────────────────────────────────────────────────
trust-but-verify - session opening
─────────────────────────────────────────────────────────────────────

I'm going to walk through your artifacts looking for places where
load-bearing claims, state, or assumptions aren't backed by a second
independent signal - and for common trust-and-safety issues that
could expose you to liability or risk to your users.

Three questions I'll be answering on your behalf:
  · Am I shipping a codebase that could get me in trouble?
  · How am I protecting myself against liability?
  · Is it safe for other users?

Let me set up the session.

Scope: <path> contains <N> files matching the code-domain triggers.
       Top by likely-impact:

         1. <file> (<N> lines · <reason>)
         2. <file> ...
         ...

       Proceed with all, or narrow scope?
       -> AskUserQuestion chips: "All files (Recommended)" · "Top 5 above" · "I'll give a path"

─────────────────────────────────────────────────────────────────────

Verification mode for this session:
  -> AskUserQuestion chips:
      "AUTO (Recommended)" - verifications (fetch a URL, query a source, run a
          tool) execute immediately; I show you each result.
      "ASK FIRST" - I describe each check and get your approval before running it.

─────────────────────────────────────────────────────────────────────

Trust & safety baseline categories (default: ALL 6 ON):
  Security · Privacy · License · Accessibility · Supply chain · Operational

  -> AskUserQuestion chips: "Keep all 6 on (Recommended)" · "Disable some"
      The six categories exceed AskUserQuestion's 4-option cap, so disabling is a
      two-step chip flow: pick "Disable some", then a follow-up multiSelect chip
      set (≤4 at a time) to choose which to drop. Each disabled category - and the
      operator's stated reason - lands in the report COVERAGE block (anti-AB-3).

─────────────────────────────────────────────────────────────────────

Setup complete.

Domain:           code
Verification:     <auto | ask-first>
Categories:       <list>
Scope:            <N> files

Sources I'm authorized to consult for this session:
  OWASP Top 10 (2021) · ASVS v4 · CWE Top 25 (MITRE)
  GDPR (gdpr-info.eu) · CCPA (oag.ca.gov) · COPPA (ftc.gov)
  SPDX License List (spdx.org)
  WCAG 2.2 (w3.org) · ARIA APG (w3.org) · Section 508 (section508.gov)
  NIST SSDF (csrc.nist.gov) · SLSA (slsa.dev) · OpenSSF Scorecard
  OWASP Cheat Sheets · NIST CSF 2.0 · CIS Controls v8
  npm registry / pip / cargo for dep verification

Starting Phase 2 scan.
```

## Format of the saved audit report

`docs/audits/AUDIT-YYYY-MM-DD-trust-but-verify.md`:

```markdown
# Trust-but-Verify Audit - <project> - <YYYY-MM-DD>

> **THIS REPORT REFLECTS ONLY THE COVERAGE ENUMERATED IN THE COVERAGE SECTION BELOW. ABSENCE OF A FINDING ELSEWHERE IS NOT EVIDENCE OF CLEAN STATE.**

**Verification mode:** <auto | ask-first>
**Categories enabled:** <list>
**Scope:** <N> files
**Skill version:** <semver of trust-but-verify at session time>

## COVERAGE (anti-AB-3 - survivorship-bias defense)

### Categories enabled this session
- security · privacy · license · ... (per Phase 1 selection)

### Categories DISABLED at Phase 1
- a11y - operator-stated reason: "backend service, no UI"
- (none) - if all enabled

### Branches WALKED
- sec-sql-injection · sec-xss · ... (full list of branch_ids checked)

### Branches CONFIRMED CLEAN (checked, no finding)
- sec-hardcoded-secret · priv-pii-in-logs · ... (operators know what was checked AND came back clean)

### Branches NOT RUN (out of scope)
- a11y-* (category disabled)
- supply-known-cve-deps (requires `pip-audit` not on PATH)

### Files / paths EXCLUDED from scope
- `data/` (operator-excluded - may contain real investigation data)
- `fixtures/` (operator-excluded)
- `vendor/`, `node_modules/`, `.venv/` (default excludes)

## RECALL BUDGET (anti-AB-3 - recall side of the survivorship-bias defense)

> The COVERAGE block above is what was looked at (precision honesty). This block
> is what the audit could NOT catch (recall honesty). Absence of a finding in
> these classes is NOT evidence of their absence. Taxonomy + the corpus that
> measures it: test-corpus/README.md.

### FN-D - out of scope this session (declared)
- <category disabled>: <operator-stated reason>
- <path / surface not scanned>: e.g. "web/ frontend - backend-only scope"
- (none) - if the scan covered the full artifact

### FN-E - vulnerability classes not modeled by ANY branch (architectural)
- timing attacks · race conditions / TOCTOU · business-logic flaws ·
  insecure deserialization · complex authorization models ·
  SSRF-by-design in fetcher architectures
- <any project-specific class the operator named at Phase 1>

### FN-A / FN-B blind spots ENCOUNTERED this session (if any)
- <branch_id>: FN-A detection-miss (pattern outside the detect regex) OR
  FN-B over-drop (verify window could not trace cross-file taint at <file>)

## Findings

###  Finding 1 · CRITICAL · security · SQL injection (CWE-89)

<full finding block as in dialogue protocol>

**Outcome:** Verified via reading the code. Fix applied (commit <sha>).

---

###  Finding 2 · HIGH · security · Missing CSRF protection

<full finding block>

**Outcome:** Accepted as trust-debt. Reason: "site is behind SSO with
short-lived tokens; CSRF risk is real but bounded. Re-review in 90 days
when we add public endpoints."

---

(continued for each finding)

## Summary

- Findings surfaced:    <N>
- Fixed in session:     <N>
- Accepted as debt:     <N>
- Skipped silently:     <N>

## Sources consulted during verification

<list of which authoritative sources the skill actually queried>

## Audit-of-the-audit (skill's self-check)

- Two-signal prefilter dropped <N> candidate findings before they entered
  the report.
- <N> findings flagged with confidence MEDIUM - listed individually below
  with operator's confirmation that they're real.
- 0 findings cited a framework section the skill couldn't reach during
  verification.
```

## The RECALL BUDGET block - required (recall-side honesty)

The audit report MUST carry a `RECALL BUDGET` block (placed in the body, directly
after `COVERAGE`). Where `COVERAGE` is the *precision* honesty surface - what was
looked at, so absence-of-finding is bounded - `RECALL BUDGET` is the *recall*
honesty surface: the false-negative classes the session could **not** catch. The
two-signal prefilter favors precision by construction; this block keeps the recall
cost **declared, not silent**. Full taxonomy and the corpus that measures it:
`test-corpus/README.md`.

**Honesty discipline (anti-AB-3, recall side):** the `FN-E` list is NOT optional
boilerplate. Reproducing the generic class list while a project-specific unmodeled
class goes unnamed is itself a survivorship-bias failure. Name what *this* artifact
plausibly contains that *no branch* checks. Closing any listed gap - a new branch
(FN-E), a widened `detect:` regex (FN-A), a deeper `verify:` step (FN-B), or wider
scope (FN-D) - should land a `test-corpus/` case that promotes a `false_negative`
to `true_positive`.

## Audit report - required trailing blocks

Every audit report MUST close with these three blocks before being considered finalized.

### REDACTIONS (anti-AB-5 - confidentiality defense)

```markdown
## REDACTIONS

Pre-write redaction pass scrubbed the following from the audit report:

| Type | Count |
|---|---|
| API keys (sk-*, xox*, AKIA*) | <N> |
| Passwords / generic credential strings | <N> |
| URLs with embedded credentials | <N> |
| Emails | <N> (or "not redacted - operator opted out") |
| Phone numbers | <N> (or "not redacted - operator opted out") |

Redactions appear in the report body as `<REDACTED: type=<...>, length=<N>>`.

If your `.gitignore` does not exclude `docs/audits/`, this report will be
committed if you `git add` the folder. Recommended: keep audit reports
out of public history or store as signed external artifacts.
```

### STALE_CITATIONS (anti-AB-1 - citation-theater defense)

```markdown
## CITATION VERIFICATION

Pre-write citation re-fetch (every URL cited in this session):

- <N> citations verified accessible + content match
-  <N> citations downgraded to "pending re-verification" (URLs below)

If any citation is stale, update `references/grounding.md` and re-run.
A citation marked "pending re-verification" means the finding's grounding
is provisional, not confirmed.

[List of stale-citation URLs, if any]
```

### ATTESTATION (anti-AB-11 - integrity defense)

```markdown
## ATTESTATION

**Finalized:** <ISO timestamp>
**Skill version:** <semver>
**Operator:** <git config user.name, if available>

**Counts** (any edit to the row block invalidates this hash):

| Metric | Value |
|---|---|
| Findings surfaced | <N> |
| Branches confirmed clean | <N> |
| Fixed WITH verification | <N> |
| Fixed via BYPASS | <N> ← surfaced separately |
| Accepted as trust-debt | <N> |
| Skipped silently | <N> |
| AMBIGUOUS (unresolved) | <N> ← re-surface next session |
| Bypass rate | <pct>% (circuit breaker fires at >50%) |

**Hash (SHA-256 of finding rows + counts):** `<sha256>`

To verify integrity: re-compute the hash of the rows + counts block. A
mismatch indicates the report has been edited post-finalization.
```

## Pause and resume

If the operator says "stop" or closes mid-walk-through, the skill writes session state to `<project>/.trust-but-verify-session.yml` capturing where in the walk-through they paused and what's queued.

`/trust-but-verify --resume` picks up where left off with the same verification mode and categories active.
