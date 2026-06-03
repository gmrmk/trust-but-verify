#!/usr/bin/env python3
"""
score.py - detection-layer harness for the trust-but-verify synthetic corpus.

WHAT IT DOES (and does NOT do)
------------------------------
This harness runs each branch's *detect:* regexes (pulled verbatim from
trust-tree.yaml) against every labeled case file, and checks whether detection
fired. It validates that each case's `expected_label` is *consistent* with what
the detection layer actually does, and computes a detection-layer confusion
matrix (precision / recall / specificity) over the planted ground truth.

It scores the DETECTION layer only - the regex pass. It cannot score the *verify*
step (that needs a human/LLM second signal), so it does not produce the full
pipeline precision/recall. Instead it enforces the consistency invariants that
make the manifest's hand-labels trustworthy:

  expected_label        required detection behavior
  ------------------    ------------------------------------------------
  true_positive         MUST fire   (real issue; detector catches it)
  false_positive        MUST fire   (bait; verify then drops it)        <- if SILENT it's really a TN
  true_negative         MUST be silent (clean; detector correctly quiet)
  false_negative FN-A   MUST be silent (detection miss - the whole point)
  false_negative FN-B   MUST fire   (detect catches it; verify over-drops)
  false_negative FN-C/D/E   n/a     (procedural - not a detect-layer claim)

A MISMATCH means either the label is wrong or the fixture doesn't do what its
note claims. Fix one or the other until the harness is green. That green is the
second signal that the corpus is honest about its own detection layer.

USAGE:  python score.py        (run from repo root or test-corpus/)
EXIT:   0 if all consistent, 1 if any mismatch.
"""
import os, re, sys, collections

# Windows consoles default to cp1252 and choke on non-ASCII; force UTF-8 so the
# report prints identically on every platform.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

def load_yaml(path):
    import yaml
    with open(path, "rb") as f:          # bytes -> PyYAML detects UTF-8
        return yaml.safe_load(f)

def branch_regexes(tree):
    """branch_id -> list of compiled regexes (skips structural:/tool-call: entries)."""
    out = {}
    for b in tree["branches"]:
        pats = []
        for entry in (b.get("detect") or []):
            s = str(entry).strip()
            if s.startswith("structural:") or s.startswith("tool-call:"):
                continue
            try:
                pats.append(re.compile(s, re.MULTILINE))
            except re.error as e:
                print(f"  ! uncompilable regex in {b['id']}: {e}", file=sys.stderr)
        out[b["id"]] = pats
    return out

def expected_detection(label, fn_class):
    """Return True (must fire), False (must be silent), or None (n/a)."""
    if label in ("true_positive", "false_positive"):
        return True
    if label == "true_negative":
        return False
    if label == "false_negative":
        if fn_class == "FN-A":
            return False          # detection miss
        if fn_class == "FN-B":
            return True           # detect fires, verify over-drops
        return None               # FN-C/D/E: procedural
    return None

def main():
    tree = load_yaml(os.path.join(ROOT, "trust-tree.yaml"))
    manifest = load_yaml(os.path.join(HERE, "manifest.yaml"))
    regexes = branch_regexes(tree)

    rows, mismatches = [], []
    # detection-layer confusion over ground_truth (vulnerable = positive class)
    conf = collections.Counter()
    per_branch = collections.defaultdict(lambda: collections.Counter())

    for c in manifest["cases"]:
        branch, label, fn = c["branch"], c["expected_label"], c.get("fn_class", "n/a")
        path = os.path.join(HERE, c["file"])
        content = open(path, "r", encoding="utf-8").read()
        pats = regexes.get(branch, [])
        fired = any(p.search(content) for p in pats)

        exp = expected_detection(label, fn)
        status = "n/a" if exp is None else ("OK" if fired == exp else "MISMATCH")
        if status == "MISMATCH":
            mismatches.append((c["id"], label, fn, "fired" if fired else "silent",
                               "should fire" if exp else "should be silent"))
        rows.append((c["id"], label, fn, "fired" if fired else "silent", status))

        # detection-layer confusion vs ground truth
        gt_pos = (c["ground_truth"] == "vulnerable")
        cell = ("TP" if gt_pos and fired else "FP" if not gt_pos and fired
                else "FN" if gt_pos and not fired else "TN")
        conf[cell] += 1
        per_branch[branch][c["expected_label"]] += 1

    # ---- report ----
    print("=" * 74)
    print("DETECTION-LAYER HARNESS - per-case")
    print("=" * 74)
    print(f"{'case':52} {'detect':7} {'check'}")
    for cid, label, fn, fired, status in rows:
        flag = "" if status in ("OK", "n/a") else "  <<< MISMATCH"
        print(f"{cid:52} {fired:7} {status}{flag}")

    print("\n" + "=" * 74)
    print("DETECTION-LAYER CONFUSION (ground_truth=vulnerable is positive)")
    print("=" * 74)
    TP, FP, FN, TN = conf["TP"], conf["FP"], conf["FN"], conf["TN"]
    prec = TP / (TP + FP) if (TP + FP) else float("nan")
    rec  = TP / (TP + FN) if (TP + FN) else float("nan")
    spec = TN / (TN + FP) if (TN + FP) else float("nan")
    print(f"  TP={TP}  FP={FP}  FN={FN}  TN={TN}")
    print(f"  detection precision   = {prec:.3f}   (of what the REGEX flags, how much is real)")
    print(f"  detection recall      = {rec:.3f}   (of real issues, how many the REGEX even sees)")
    print(f"  detection specificity = {spec:.3f}   (of clean code, how much the REGEX leaves alone)")
    print("  NOTE: this is the regex pass only. The verify step then trims FPs;")
    print("        the FN cases here are the recall the verify step can never recover.")

    print("\n" + "=" * 74)
    print("PER-BRANCH CLASS BALANCE (expected_label)")
    print("=" * 74)
    labels = ["true_positive", "false_positive", "false_negative", "true_negative"]
    print(f"{'branch':32} {'TP':>3} {'FP':>3} {'FN':>3} {'TN':>3}")
    for b in sorted(per_branch):
        pc = per_branch[b]
        print(f"{b:32} {pc['true_positive']:>3} {pc['false_positive']:>3} "
              f"{pc['false_negative']:>3} {pc['true_negative']:>3}")

    print("\n" + "=" * 74)
    if mismatches:
        print(f"RESULT: {len(mismatches)} MISMATCH(es) - label vs actual detection disagree:")
        for cid, label, fn, got, want in mismatches:
            print(f"  - {cid}: labeled {label}/{fn} but detection {got} ({want})")
        print("\nFix the label or the fixture. A 'false_positive' that stays SILENT is")
        print("really a 'true_negative' (the regex's own specificity handled it).")
        return 1
    print("RESULT: all cases consistent with their detection-layer behavior. [PASS]")
    return 0

if __name__ == "__main__":
    sys.exit(main())
