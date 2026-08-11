#!/usr/bin/env python3
"""
check_branch_schema.py - mechanized branch-schema gate for trust-tree.yaml.

WHY THIS EXISTS
---------------
SKILL.md and trust-tree.yaml both declare branch requirements as NON-NEGOTIABLE
("a branch with an empty framework: MUST NOT ship", "grounding is the gate, not
the polish"). Until this script existed those were instructions to a reader, not
constraints on the artifact - the exact "claim without a second signal" the skill
is built to refuse. This gate is the second signal on the skill's own tree.

WHAT IT ENFORCES
----------------
  1. Branch ids are unique and every branch names a known category.
  2. Every branch has a non-empty question / detect / verify / severity /
     last_verified.
  3. Every `framework:` entry resolves to an id in `baseline_frameworks:`.
  4. In-repo (non-external) frameworks may be cited ONLY by epistemic branches -
     a security or privacy branch may never ground itself in this repo.
  5. `verify:` is not a restatement of `detect:` (the independence property).
  6. `last_verified:` is an ISO date, not in the future.
  7. Non-epistemic branches carry a liability_template with the key pair their
     category requires (a11y uses the accessibility-framed variant).
  8. Every regex in `detect:` compiles.
  9. `rca_defaults:` covers exactly the set of branch ids - no gaps, no orphans.
 10. Every branch has at least one labeled corpus case (the roadmap re-entry
     rule: a branch without a test case is unmeasured).
 11. Every corpus case points at a file/dir that exists on disk.
 12. Every framework URL in the registry also appears in references/grounding.md
     (registry and grounding cannot drift apart silently).

USAGE:  python scripts/check_branch_schema.py
EXIT:   0 if every invariant holds, 1 otherwise.
"""
import os
import re
import sys
import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SKILL = os.path.join(ROOT, "skills", "trust-but-verify")
TREE = os.path.join(SKILL, "trust-tree.yaml")
GROUNDING = os.path.join(SKILL, "references", "grounding.md")
CORPUS = os.path.join(ROOT, "test-corpus")

CATEGORIES = {"security", "privacy", "license", "a11y",
              "supply_chain", "operational", "epistemic"}
SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}

# Categories whose liability block uses the accessibility-framed variant
# (dialogue-protocol.md § "The Liability Framing block").
A11Y_KEYS = {"users_affected", "wcag_criterion"}
BASE_KEYS = {"user_harm", "legal_exposure"}


def load(path):
    import yaml
    with open(path, "rb") as f:
        return yaml.safe_load(f)


def main():
    errors = []

    def err(msg):
        errors.append(msg)

    tree = load(TREE)
    branches = tree.get("branches") or []

    # ── framework registry ────────────────────────────────────────────────
    registry = {}
    for cat, entries in (tree.get("baseline_frameworks") or {}).items():
        for f in entries or []:
            fid = f.get("id")
            if not fid:
                err(f"baseline_frameworks.{cat}: entry with no id")
                continue
            if fid in registry:
                err(f"baseline_frameworks: duplicate id {fid!r}")
            registry[fid] = dict(f, _category=cat)

    # An in-repo framework is first-party doctrine, not an external standard.
    in_repo = {fid for fid, f in registry.items() if f.get("external") is False}

    # ── per-branch invariants ─────────────────────────────────────────────
    seen = set()
    for b in branches:
        bid = b.get("id") or "<no id>"
        if bid in seen:
            err(f"{bid}: duplicate branch id")
        seen.add(bid)

        cat = b.get("category")
        if cat not in CATEGORIES:
            err(f"{bid}: unknown category {cat!r}")

        for field in ("question", "verify", "severity", "last_verified"):
            if not b.get(field):
                err(f"{bid}: missing or empty {field}:")

        if b.get("severity") not in SEVERITIES:
            err(f"{bid}: severity {b.get('severity')!r} not one of {sorted(SEVERITIES)}")

        detect = b.get("detect") or []
        if not detect:
            err(f"{bid}: missing or empty detect:")

        # (3) + (4) grounding
        fws = b.get("framework") or []
        if not fws:
            err(f"{bid}: empty framework: - a branch without grounding MUST NOT ship")
        for f in fws:
            if not isinstance(f, str):
                err(f"{bid}: framework entry {f!r} is not a registry id "
                    f"(use an id from baseline_frameworks:)")
                continue
            if f not in registry:
                err(f"{bid}: framework id {f!r} is not in baseline_frameworks:")
            elif f in in_repo and cat != "epistemic":
                err(f"{bid}: category {cat!r} cites in-repo framework {f!r} - "
                    f"only epistemic branches may ground in this repo")

        # (5) verify independence (heuristic, but catches copy-paste)
        verify = str(b.get("verify") or "")
        if verify and len(verify.strip()) < 25:
            err(f"{bid}: verify: is too short to be a falsifiable check: {verify!r}")
        for d in detect:
            if verify.strip() and verify.strip() == str(d).strip():
                err(f"{bid}: verify: restates detect: - not an independent signal")

        # (6) last_verified is a real, non-future date
        lv = b.get("last_verified")
        if lv:
            try:
                d = datetime.date.fromisoformat(str(lv))
                if d > datetime.date.today():
                    err(f"{bid}: last_verified {lv} is in the future")
            except ValueError:
                err(f"{bid}: last_verified {lv!r} is not an ISO date (YYYY-MM-DD)")

        # (7) liability template
        if cat != "epistemic":
            lt = b.get("liability_template") or {}
            if not lt:
                err(f"{bid}: missing liability_template:")
            else:
                want = A11Y_KEYS if cat == "a11y" else BASE_KEYS
                missing = [k for k in want if not lt.get(k)]
                if missing:
                    err(f"{bid}: liability_template missing {missing}")

        # (8) regexes compile
        for d in detect:
            s = str(d).strip()
            if s.startswith("structural:") or s.startswith("tool-call:"):
                continue
            try:
                re.compile(s)
            except re.error as e:
                err(f"{bid}: uncompilable detect regex {s!r}: {e}")

    branch_ids = {b.get("id") for b in branches}

    # (9) rca_defaults coverage
    rca = set((tree.get("rca_defaults") or {}).keys())
    for missing in sorted(branch_ids - rca):
        err(f"rca_defaults: no entry for branch {missing}")
    for orphan in sorted(rca - branch_ids):
        err(f"rca_defaults: entry {orphan} refers to no branch")

    # ── (10) + (11) corpus coverage ───────────────────────────────────────
    regex_manifest = load(os.path.join(CORPUS, "manifest.yaml"))
    struct_manifest = load(os.path.join(CORPUS, "structural", "manifest.yaml"))

    covered = set()
    for c in regex_manifest.get("cases") or []:
        covered.add(c.get("branch"))
        p = os.path.join(CORPUS, c.get("file", ""))
        if not os.path.isfile(p):
            err(f"corpus case {c.get('id')}: file not found: {c.get('file')}")
    for c in struct_manifest.get("cases") or []:
        covered.add(c.get("branch"))
        p = os.path.join(CORPUS, "structural", c.get("dir", ""))
        if not os.path.isdir(p):
            err(f"corpus case {c.get('id')}: dir not found: {c.get('dir')}")

    for uncovered in sorted(branch_ids - covered):
        err(f"{uncovered}: no labeled corpus case - a branch without a test case "
            f"is an unmeasured claim")
    for orphan in sorted(covered - branch_ids):
        err(f"corpus references branch {orphan!r} that is not in trust-tree.yaml")

    # ── (12) registry vs grounding.md ─────────────────────────────────────
    with open(GROUNDING, encoding="utf-8") as f:
        grounding = f.read()
    for fid, meta in sorted(registry.items()):
        if meta.get("external") is False:
            continue
        url = meta.get("url", "")
        if url and url not in grounding:
            err(f"grounding.md: no entry for registry framework {fid} ({url})")

    # ── report ────────────────────────────────────────────────────────────
    print("=" * 74)
    print("BRANCH-SCHEMA GATE - trust-tree.yaml")
    print("=" * 74)
    print(f"  branches:            {len(branches)}")
    print(f"  registered frameworks: {len(registry)} "
          f"({len(in_repo)} in-repo, {len(registry) - len(in_repo)} external)")
    print(f"  branches with corpus cases: {len(branch_ids & covered)} of {len(branch_ids)}")
    print()

    if errors:
        print(f"RESULT: {len(errors)} violation(s):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("RESULT: every branch satisfies the schema gate. [PASS]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
