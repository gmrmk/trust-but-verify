#!/usr/bin/env python3
"""
verify_score.py - full-pipeline (detect + verify) scorer for the corpus.

`score.py` and `structural/score_structural.py` score the DETECTION layer (does
the regex/predicate fire?). This scorer goes one layer further: it scores the
FULL pipeline (detect THEN verify), where the unit of truth is "did the skill
end up SURFACING a finding?" - which is what an operator actually experiences.

It has two modes:

1. DESIGNED mode (no run log) - computes the corpus's *intended* full-pipeline
   metrics from the labels alone. A correct skill surfaces a finding ONLY for
   `true_positive` cases: `false_positive` cases are dropped at verify,
   `true_negative` cases never detect, `false_negative` cases are the known
   misses. So the designed confusion is:
       TP = |true_positive|   FP = 0   FN = |false_negative|
       TN = |false_positive| + |true_negative|
   This is the corpus's RECALL CEILING: designed recall = TP/(TP+FN), and the
   FN cases are the promotable headroom (promote one -> recall rises).

2. ACTUAL mode (with a run log) - a run log records, per case, what the skill
   ACTUALLY did (`surfaced: true|false` after detect+verify). The scorer computes
   the real confusion (surfaced vs ground_truth) and diffs it against the design:
   which `false_positive` cases LEAKED (verify failed to drop -> real FP), which
   `true_positive` cases were MISSED, and which `false_negative` cases were
   unexpectedly CAUGHT (recall promotions). That gap is the verify step's report
   card - the thing the detection harness cannot see.

USAGE:
    python test-corpus/verify_score.py                 # designed mode
    python test-corpus/verify_score.py runs/<log>.yaml # designed + actual + gap
"""
import os, sys, collections

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))

def load(path):
    import yaml
    with open(path, "rb") as f:
        return yaml.safe_load(f)

def all_cases():
    cases = list(load(os.path.join(HERE, "manifest.yaml"))["cases"])
    cases += list(load(os.path.join(HERE, "structural", "manifest.yaml"))["cases"])
    return cases

def f_beta(precision, recall, beta=2.0):
    b2 = beta * beta
    denom = b2 * precision + recall
    return ((1 + b2) * precision * recall / denom) if denom else float("nan")

def metrics(tp, fp, fn, tn):
    prec = tp / (tp + fp) if (tp + fp) else float("nan")
    rec  = tp / (tp + fn) if (tp + fn) else float("nan")
    spec = tn / (tn + fp) if (tn + fp) else float("nan")
    return prec, rec, spec, f_beta(prec, rec, 2.0)

def show(title, tp, fp, fn, tn):
    prec, rec, spec, f2 = metrics(tp, fp, fn, tn)
    print(f"  {title}")
    print(f"    TP={tp}  FP={fp}  FN={fn}  TN={tn}")
    print(f"    precision={prec:.3f}  recall={rec:.3f}  specificity={spec:.3f}  F2={f2:.3f}")
    return prec, rec, f2

def main():
    cases = {c["id"]: c for c in all_cases()}
    bylabel = collections.Counter(c["expected_label"] for c in cases.values())

    # ── DESIGNED ──
    d_tp = bylabel["true_positive"]
    d_fp = 0
    d_fn = bylabel["false_negative"]
    d_tn = bylabel["false_positive"] + bylabel["true_negative"]

    print("=" * 74)
    print("VERIFY-LAYER SCORER - full pipeline (detect + verify)")
    print("=" * 74)
    print(f"corpus: {len(cases)} cases  "
          f"(TP-label={bylabel['true_positive']} FP-label={bylabel['false_positive']} "
          f"FN-label={bylabel['false_negative']} TN-label={bylabel['true_negative']})\n")

    print("DESIGNED full-pipeline metrics (the ceiling a correct skill should hit):")
    show("if verify is perfect (drops every FP-bait, surfaces every TP):", d_tp, d_fp, d_fn, d_tn)
    print("    NOTE: designed precision is 1.0 by construction (a correct verify never")
    print("    surfaces a benign case). Designed recall < 1.0 because the corpus plants")
    print("    false_negative cases on purpose - those are the documented blind spots.")

    # promotable-FN headroom
    fn_cases = [c for c in cases.values() if c["expected_label"] == "false_negative"]
    by_class = collections.Counter(c.get("fn_class", "n/a") for c in fn_cases)
    by_branch = collections.Counter(c["branch"] for c in fn_cases)
    print(f"\nPROMOTABLE-FN headroom: {len(fn_cases)} false_negative cases "
          f"(each promotion -> recall rises)")
    print(f"  by fn_class: {dict(by_class)}")
    print(f"  FN-A (detection/structural reach gaps - widen a regex/predicate): "
          f"{by_class.get('FN-A', 0)}")
    print(f"  FN-B (verify over-drops - deepen the verify step):                "
          f"{by_class.get('FN-B', 0)}")
    top = ", ".join(f"{b}:{n}" for b, n in by_branch.most_common(5))
    print(f"  most blind branches: {top}")

    # ── ACTUAL (if a run log is given) ──
    if len(sys.argv) < 2:
        print("\n" + "=" * 74)
        print("No run log given -> designed mode only. To score an ACTUAL run:")
        print("  python test-corpus/verify_score.py runs/<run-log>.yaml")
        print("A run log records `surfaced: true|false` per case_id (see runs/sample-run.yaml).")
        return 0

    log = load(sys.argv[1])
    results = {r["case_id"]: bool(r["surfaced"]) for r in log.get("results", [])}
    missing = [cid for cid in cases if cid not in results]
    extra = [cid for cid in results if cid not in cases]

    a_tp = a_fp = a_fn = a_tn = 0
    leaks, missed_tp, promotions = [], [], []
    for cid, c in cases.items():
        if cid not in results:
            continue
        surfaced = results[cid]
        vuln = (c["ground_truth"] == "vulnerable")
        if surfaced and vuln: a_tp += 1
        elif surfaced and not vuln:
            a_fp += 1; leaks.append((cid, c["expected_label"]))
        elif not surfaced and vuln:
            a_fn += 1
        else: a_tn += 1
        # gap vs design
        if c["expected_label"] == "true_positive" and not surfaced:
            missed_tp.append(cid)
        if c["expected_label"] == "false_negative" and surfaced:
            promotions.append((cid, c.get("fn_class", "n/a")))

    print("\n" + "=" * 74)
    print(f"ACTUAL full-pipeline metrics - run log: {os.path.basename(sys.argv[1])}")
    print("=" * 74)
    if missing:
        print(f"   {len(missing)} corpus case(s) absent from the run log "
              f"(not scored): e.g. {missing[:3]}")
    if extra:
        print(f"   {len(extra)} run-log entry/entries not in the corpus (ignored): {extra[:3]}")
    a_prec, a_rec, a_f2 = show("observed (surfaced vs ground_truth):", a_tp, a_fp, a_fn, a_tn)

    print("\nGAP vs DESIGN (what the verify step did to the recall/precision):")
    if leaks:
        print(f"  VERIFY LEAKS - benign cases the skill wrongly surfaced (real FPs): {len(leaks)}")
        for cid, lbl in leaks:
            print(f"    - {cid}  (labeled {lbl}; verify failed to drop it -> precision cost)")
    else:
        print("  VERIFY LEAKS: none - verify dropped every false_positive bait. ")
    if promotions:
        print(f"  RECALL PROMOTIONS - false_negative cases the skill actually CAUGHT: {len(promotions)}")
        for cid, fn in promotions:
            print(f"    - {cid}  ({fn} blind spot closed -> recall gain; update the manifest label)")
    else:
        print("  RECALL PROMOTIONS: none this run.")
    if missed_tp:
        print(f"  MISSED TPs - true_positive cases the skill failed to surface: {len(missed_tp)}")
        for cid in missed_tp:
            print(f"    - {cid}  (detect or verify regressed -> investigate)")
    else:
        print("  MISSED TPs: none - every planted true positive was surfaced. ")

    print("\n  Δ recall  (actual − designed): "
          f"{a_rec - (d_tp/(d_tp+d_fn) if (d_tp+d_fn) else 0):+.3f}")
    print("  Δ precision (vs designed 1.000): "
          f"{a_prec - 1.0:+.3f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
