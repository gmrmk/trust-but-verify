# Grounding - Authoritative Framework Citations

Every check in `trust-tree.yaml` cites at least one framework from this registry. **If a check cannot cite a real authoritative source, it does not ship** - that's the discipline applied recursively to the skill itself.

This file is the single source of truth for what the skill considers "official." It is intentionally small in v0.1 - Kaizen says we add citations only when a branch actually uses them.

> **ANTI-AB-1 (citation theater) DEFENSE.** Every citation below carries `version:` and `verified_accessible:` fields. Before any release of trust-but-verify, every URL MUST be re-fetched and the content match re-confirmed. Stale citations block release. Phase 4 of every audit session also re-fetches the URLs used during the session and flags `STALE_CITATIONS:` in the report. **A citation marked "pending re-verification" means the finding's grounding is provisional, not confirmed.**

---

## Category 1 - Security

| Framework | Version | Authority | URL | Verified accessible | Next expected revision |
|-----------|---------|-----------|-----|---------------------|------------------------|
| OWASP Top 10 | 2021 | OWASP | https://owasp.org/Top10/ | 2026-05-25 | 2025-2026 (OWASP ~4yr cadence; check for 2025 edition) |
| OWASP Application Security Verification Standard | v4 | OWASP | https://owasp.org/www-project-application-security-verification-standard/ | 2026-05-25 | v5 in draft (check ASVS GitHub) |
| CWE Top 25 Most Dangerous Software Weaknesses | 2024 | MITRE Corporation | https://cwe.mitre.org/top25/ | 2026-05-25 | Annual update - re-verify yearly |
| OWASP Cheat Sheet Series | continuously updated | OWASP | https://cheatsheetseries.owasp.org/ | 2026-05-25 | Continuous |

**Used by branches:** `sec-sql-injection`, `sec-xss`, `sec-broken-access-control`, `sec-hardcoded-secret`, `sec-ssrf`, `sec-weak-crypto`, `op-stack-trace-leakage`, `op-no-rate-limit`.

---

## Category 2 - Privacy & data handling

| Framework | Version | Authority | URL | Verified accessible | Next expected revision |
|-----------|---------|-----------|-----|---------------------|------------------------|
| GDPR | EU 2016/679 (in force 2018-05-25) | European Union | https://gdpr-info.eu/ | 2026-05-25 | Stable text; check eur-lex.europa.eu for amendments |
| CCPA / CPRA | CPRA effective 2023-01-01 | California Office of the Attorney General | https://oag.ca.gov/privacy/ccpa | 2026-05-25 | Regs updated annually - re-verify yearly |
| COPPA | last major update 2013 | US Federal Trade Commission | https://www.ftc.gov/legal-library/browse/rules/childrens-online-privacy-protection-rule-coppa | 2026-05-25 | FTC reviewing 2024; check for 2026 revision |

**Used by branches:** `priv-pii-in-logs`, `priv-no-data-rights`, `priv-pii-plaintext`.

**Key articles cited in liability framing:**
- GDPR Art. 5(1)(c) - data minimization
- GDPR Art. 17 - right to erasure
- GDPR Art. 20 - right to data portability
- GDPR Art. 25 - privacy by design
- GDPR Art. 32 - security of processing
- GDPR Art. 33-34 - breach notification

**Note:** This skill cites legal frameworks. It is NOT legal advice. Interpretation belongs to qualified counsel.

---

## Category 3 - License & IP

| Framework | Version | Authority | URL | Verified accessible | Next expected revision |
|-----------|---------|-----------|-----|---------------------|------------------------|
| SPDX License List | 3.24+ (continuously updated) | Linux Foundation | https://spdx.org/licenses/ | 2026-05-25 | Continuous additions; re-verify quarterly |

**Used by branches:** `license-dep-conflict`, `license-missing-attribution`.

**Key compatibility considerations:**
- **CC0 / Public Domain:** frictionless, no attribution required
- **CC-BY 3.0 / 4.0:** usable, requires attribution (NOTICE / CREDITS)
- **CC-BY-SA:** usable for assets; derivative work inherits SA
- **GPL 3.0:** usable for assets; do NOT copy GPL code into non-GPL projects (taint risk)
- **AGPL 3.0:** taint extends to SaaS use (running the software networked counts as distribution)
- **Custom "free for personal use":** generally NOT usable commercially without explicit permission

---

## Category 4 - Accessibility

| Framework | Version | Authority | URL | Verified accessible | Next expected revision |
|-----------|---------|-----------|-----|---------------------|------------------------|
| WCAG | 2.2 Level AA (W3C Rec 2023-10-05) | W3C | https://www.w3.org/TR/WCAG22/ | 2026-05-25 | WCAG 3.0 in working draft - multi-year stable |
| WAI-ARIA Authoring Practices Guide | continuously updated | W3C | https://www.w3.org/WAI/ARIA/apg/ | 2026-05-25 | Continuous |
| Section 508 (US Federal) | revised 2017 (current) | US General Services Administration | https://www.section508.gov/ | 2026-05-25 | Stable; check periodically |

**Used by branches:** `a11y-missing-alt`, `a11y-form-no-labels`, `a11y-color-contrast`.

**Key WCAG criteria cited in v0.1:**
- 1.1.1 Non-text Content (Level A) - alt text
- 1.4.3 Contrast (Minimum) (Level AA) - 4.5:1 normal / 3:1 large
- 3.3.2 Labels or Instructions (Level A) - form labels
- 4.1.2 Name, Role, Value (Level A) - ARIA

**Legal context** (US, varies by jurisdiction):
- ADA Title III - inaccessible websites have been ruled "places of public accommodation" (Domino's Pizza v. Robles, 9th Cir. 2019). Specific liability depends on jurisdiction.
- Section 508 - required for US federal procurement.
- EAA (EU Accessibility Act) - applies in member states from 2025.

---

## Category 5 - Supply chain

| Framework | Version | Authority | URL | Verified accessible | Next expected revision |
|-----------|---------|-----------|-----|---------------------|------------------------|
| NIST Secure Software Development Framework | SP 800-218 v1.1 (2022-02) | US National Institute of Standards and Technology | https://csrc.nist.gov/Projects/ssdf | 2026-05-25 | NIST 2-3yr cadence - check CSRC |
| SLSA | v1.0 (2023-04) | Open Source Security Foundation | https://slsa.dev/ | 2026-05-25 | Active development - check slsa.dev |
| OpenSSF Scorecard | continuously updated | OpenSSF | https://github.com/ossf/scorecard | 2026-05-25 | Continuous |

**Used by branches:** `supply-actions-floating-tag`, `supply-lockfile-missing`, `supply-known-cve-deps`.

**OpenSSF Scorecard checks referenced:**
- Pinned-Dependencies - Actions and deps pinned to SHA, not floating tags
- Security-Policy - SECURITY.md present
- Branch-Protection - main branch protected
- Code-Review - required reviews before merge
- Token-Permissions - minimal GITHUB_TOKEN permissions in workflows

---

## Category 6 - Operational safety

| Framework | Version | Authority | URL | Verified accessible | Next expected revision |
|-----------|---------|-----------|-----|---------------------|------------------------|
| OWASP Cheat Sheet Series | continuously updated | OWASP | https://cheatsheetseries.owasp.org/ | 2026-05-25 | Continuous |
| NIST Cybersecurity Framework | 2.0 (released 2024-02) | US NIST | https://www.nist.gov/cyberframework | 2026-05-25 | NIST ~5yr cadence - next major rev mid-decade |
| CIS Controls | v8.1 (current) | Center for Internet Security | https://www.cisecurity.org/controls/v8 | 2026-05-25 | Periodic minor revs - check cisecurity.org |

**Used by branches:** `op-missing-security-md`, `op-stack-trace-leakage`, `op-no-rate-limit`.

---

## Epistemic category (the original t-b-v doctrine)

The category that started the skill - pre-T&S-baseline.

| Registry id | Source | URL | External? |
|-------------|--------|-----|-----------|
| `tbv-uncertainty-protocol` | The trust-but-verify doctrine | in-repo `SKILL.md` § Philosophy | **No** |

**Used by branches:** `epi-hedged-language`, `epi-unverified-external`, `epi-state-mutation-no-readback`.

This entry is registered in `trust-tree.yaml` under `baseline_frameworks.epistemic`
with `external: false`, so epistemic branches cite a registry id like every other
branch instead of an ad-hoc string. The flag is load-bearing:
`scripts/check_branch_schema.py` allows an `external: false` framework to be cited
**only** by an `epistemic` branch. A security, privacy, license, a11y,
supply-chain, or operational branch that tried to ground itself in this repo's own
prose would fail CI - which is the point. Grounding a safety check in your own
say-so is the fabricated-grounding failure wearing a citation.

`scripts/check_citations.py` verifies this entry by resolving the repo-relative
path rather than fetching a URL.

---

## Rules for adding a new citation

When a new branch in `trust-tree.yaml` needs a new framework, add the framework here FIRST. Every entry MUST satisfy ALL of:

1. **Maintained by a recognized authority** - government agency, established standards body (W3C, ISO, ANSI, IEEE), well-known professional organization, or peer-reviewed standards group. Blog posts, vendor marketing, and community wikis MUST NOT be cited.
2. **Current** - the `version:` field MUST name the current authoritative version. `verified_accessible:` MUST be set to the ISO date the URL was last successfully fetched + content-matched.
3. **Specific** - the citation MUST reference a specific section, control identifier, or rule (`A03:2021-Injection`, `WCAG 2.2 § 1.4.3`, etc.), not "see [whole framework]."
4. **Permanently linkable** - the URL MUST be a stable canonical URL. Search results, tweets, and ephemeral URLs MUST NOT be cited.
5. **Re-verifiable in CI** - every URL added here is fetched and content-matched by `scripts/check_citations.py` as part of the release-quality gate (anti-AB-1). Entries that cannot be re-verified MUST be removed from the registry. Add the framework to `baseline_frameworks:` in `trust-tree.yaml` as well as to the table above - `scripts/check_branch_schema.py` fails if the registry and this file disagree.

If a check cannot satisfy ALL FIVE rules, the skill MUST surface the finding as AMBIGUOUS and ask the operator how to proceed. Citing an unofficial source to make a finding land is a Quality-bar violation (see SKILL.md § *"No fabricated grounding"*).

## Release-time verification (anti-AB-1)

Before any release of trust-but-verify, every URL in this file MUST be:

1. Fetched and confirmed reachable
2. Content-matched: a distinctive token from the framework name MUST appear in the fetched body
3. Re-stamped with the new `verified_accessible:` date

A release with stale citations MUST NOT ship. See `references/anti-behaviors.md` § AB-1 for the full defense spec.

**This is mechanized, not honour-system.** `scripts/check_citations.py` performs steps 1 and 2; `.github/workflows/citations.yml` runs it weekly, on demand, and on every `v*` release tag (with `--strict`, which escalates a content-match miss into a failure). Step 3 is still a human edit - re-stamp the dates in the tables above when a release run passes.

Two calibrations in that script are worth knowing, because both were learned by running it:

- **A 403 or 429 is not staleness.** It means the host refused *this client* - bot protection, a WAF, a corporate proxy - and says nothing about whether the document exists. `ftc.gov` serves 403 to a non-browser user-agent and 200 to a browser one. Only a 404/410, or a connection that never completes, proves a citation is gone. Blocked responses are reported as BLOCKED for a human to confirm, never counted as failures.
- **Liveness is not a pull-request gate.** A network fetch in the PR gate lets one government host's outage block an unrelated merge, and the team learns to click past a red check - which is AB-9 (bypass normalization) manufactured by our own tooling. Hence the schedule-plus-release cadence.
