#!/usr/bin/env python3
"""
score_structural.py - structural harness for the trust-but-verify corpus.

Counterpart to ../score.py. Where score.py validates branches whose `detect:` is
a single-file REGEX, this harness validates branches whose `detect:` is
STRUCTURAL (repo shape: a missing lockfile, an absent SECURITY.md, an
un-attributed vendored dependency) or TOOL-CALL.

A fixture here is therefore not one file but a MINI-REPO directory. "Detection"
is a Python predicate over that directory, registered in PREDICATES below. The
harness runs the predicate and enforces the same label-consistency invariants as
the regex harness:

  expected_label        predicate (detection) must...
  ------------------    ----------------------------------------
  true_positive         fire   (structural problem really present)
  false_positive        fire   (structure trips the check; verify then drops)
  true_negative         be silent (clean repo shape)
  false_negative FN-A   be silent (structural miss - the check can't see it)
  false_negative FN-B   fire   (check fires; a deeper verify over-drops)

To extend coverage to another structural branch: add a predicate to PREDICATES
keyed by its trust-tree.yaml branch id, drop mini-repo fixtures under
cases/<branch-id>/<label>-NN-<slug>/, and add manifest entries.

USAGE:  python test-corpus/structural/score_structural.py
EXIT:   0 if all consistent, 1 if any mismatch.
"""
import os, sys, glob, json, re as _re

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))

def has(repo, *rel):
    return any(os.path.exists(os.path.join(repo, r)) for r in rel)

def find(repo, pattern):
    return glob.glob(os.path.join(repo, pattern), recursive=True)

def _read(path):
    try:
        return open(path, encoding="utf-8", errors="ignore").read()
    except Exception:
        return ""

def _read_json(path):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return None

# ── predicate registry: branch_id -> fn(repo_dir) -> bool (does detection fire?) ──

def p_supply_lockfile_missing(repo):
    """A package manifest is committed but its lockfile is not."""
    pairs = {
        "package.json": ["package-lock.json", "yarn.lock", "pnpm-lock.yaml"],
        "Cargo.toml":   ["Cargo.lock"],
        "pyproject.toml": ["poetry.lock", "uv.lock", "pdm.lock"],
        "Pipfile":      ["Pipfile.lock"],
        "go.mod":       ["go.sum"],
    }
    for manifest, locks in pairs.items():
        if has(repo, manifest) and not has(repo, *locks):
            return True
    return False

def p_op_missing_security_md(repo):
    """No SECURITY.md at the repo root or under .github/."""
    return not has(repo, "SECURITY.md", os.path.join(".github", "SECURITY.md"))

def p_license_missing_attribution(repo):
    """A vendored/third-party LICENSE is present but no root attribution file is."""
    vendored_license = bool(
        find(repo, "vendor/**/LICENSE*") + find(repo, "third_party/**/LICENSE*")
    )
    attribution = has(repo, "NOTICE", "CREDITS.md", "CREDITS", "THIRD_PARTY_LICENSES")
    return vendored_license and not attribution

def p_license_dep_conflict(repo):
    """A dependency declares a copyleft (GPL/AGPL) license while the project is
    permissive. Naive substring check - deliberately cannot parse an SPDX
    'OR' expression (that gap is the FP case)."""
    proj = _read_json(os.path.join(repo, "package.json")) or {}
    if "GPL" in str(proj.get("license", "")).upper():     # project itself copyleft
        return False
    for pj in find(repo, "node_modules/*/package.json"):
        if "GPL" in str((_read_json(pj) or {}).get("license", "")).upper():
            return True
    return False

def p_a11y_color_contrast(repo):
    """A CSS rule pairs a foreground + background HEX colour below WCAG AA 4.5:1."""
    def lum(hex6):
        r, g, b = (int(hex6[i:i+2], 16) for i in (0, 2, 4))
        def ch(c):
            cs = c / 255
            return cs / 12.92 if cs <= 0.03928 else ((cs + 0.055) / 1.055) ** 2.4
        return 0.2126*ch(r) + 0.7152*ch(g) + 0.0722*ch(b)
    for css in find(repo, "**/*.css"):
        for block in _re.findall(r"\{([^}]*)\}", _read(css)):
            fg = _re.search(r"(?<!-)\bcolor:\s*#([0-9a-fA-F]{6})", block)
            bg = _re.search(r"background(?:-color)?:\s*#([0-9a-fA-F]{6})", block)
            if fg and bg:
                l1, l2 = lum(fg.group(1)), lum(bg.group(1))
                if (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05) < 4.5:
                    return True
    return False

def p_supply_known_cve_deps(repo):
    """A captured `npm audit --json` report lists >=1 vulnerability. The live
    branch runs the tool; the corpus pins the captured output for determinism."""
    rep = _read_json(os.path.join(repo, "audit-report.json"))
    if not rep:
        return False
    v = (rep.get("metadata") or {}).get("vulnerabilities") or {}
    return sum(int(v.get(k, 0)) for k in ("low", "moderate", "high", "critical")) > 0

def p_priv_no_data_rights(repo):
    """The app references user PII but exposes no deletion/export route."""
    routes = "\n".join(_read(p) for p in
                       find(repo, "routes/**/*.js") + find(repo, "routes/*.js"))
    has_pii = bool(_re.search(r"(user|profile|account|customer|email|patient)", routes, _re.I))
    has_rights = bool(_re.search(r"(delete[-_]?account|/delete|/export|exportdata|/gdpr)",
                                 routes, _re.I))
    return has_pii and not has_rights

def p_priv_pii_plaintext(repo):
    """A schema declares a PII column with a plaintext type and no encryption marker."""
    pii = r"(ssn|social_security|email|phone|date_of_birth|\bdob\b|address|credit_card)"
    for sql in find(repo, "**/*.sql"):
        for line in _read(sql).splitlines():
            if _re.search(pii, line, _re.I) and _re.search(r"\b(varchar|text|char)\b", line, _re.I):
                if not _re.search(r"(encrypt|pgcrypto|bytea|_enc\b|vault)", line, _re.I):
                    return True
    return False

def p_op_no_rate_limit(repo):
    """An auth route file defines a login/signup/reset endpoint with no rate-limit
    middleware in that file."""
    for f in find(repo, "routes/**/*.js") + find(repo, "routes/*.js"):
        text = _read(f)
        if _re.search(r"['\"]/?(login|signin|signup|register|forgot|reset|auth)\b", text, _re.I):
            if not _re.search(r"(ratelimit|rate_limit|express-rate-limit|slowdown|throttle|limiter)",
                              text, _re.I):
                return True
    return False

def p_supply_actions_excessive_permissions(repo):
    """A GitHub Actions workflow declares no `permissions:` block (inherits the
    repo default, often write) or grants `permissions: write-all`."""
    for wf in find(repo, ".github/workflows/*.yml") + find(repo, ".github/workflows/*.yaml"):
        text = _read(wf)
        if "permissions:" not in text:
            return True
        if _re.search(r"permissions:\s*write-all", text):
            return True
    return False

PREDICATES = {
    "supply-lockfile-missing": p_supply_lockfile_missing,
    "op-missing-security-md": p_op_missing_security_md,
    "license-missing-attribution": p_license_missing_attribution,
    "license-dep-conflict": p_license_dep_conflict,
    "a11y-color-contrast": p_a11y_color_contrast,
    "supply-known-cve-deps": p_supply_known_cve_deps,
    "priv-no-data-rights": p_priv_no_data_rights,
    "priv-pii-plaintext": p_priv_pii_plaintext,
    "op-no-rate-limit": p_op_no_rate_limit,
    "supply-actions-excessive-permissions": p_supply_actions_excessive_permissions,
}

def expected_detection(label, fn):
    if label in ("true_positive", "false_positive"):
        return True
    if label == "true_negative":
        return False
    if label == "false_negative":
        return True if fn == "FN-B" else (False if fn == "FN-A" else None)
    return None

def main():
    import yaml
    with open(os.path.join(HERE, "manifest.yaml"), "rb") as f:
        manifest = yaml.safe_load(f)

    rows, mismatches = [], []
    import collections
    per_branch = collections.defaultdict(collections.Counter)

    for c in manifest["cases"]:
        branch, label, fn = c["branch"], c["expected_label"], c.get("fn_class", "n/a")
        repo = os.path.join(HERE, c["dir"])
        pred = PREDICATES.get(branch)
        if pred is None:
            rows.append((c["id"], label, "NO-PREDICATE", "skip")); continue
        if not os.path.isdir(repo):
            rows.append((c["id"], label, "MISSING-DIR", "MISMATCH"))
            mismatches.append((c["id"], "fixture dir not found")); continue
        fired = bool(pred(repo))
        exp = expected_detection(label, fn)
        status = "n/a" if exp is None else ("OK" if fired == exp else "MISMATCH")
        if status == "MISMATCH":
            mismatches.append((c["id"], f'predicate {"fired" if fired else "silent"}, '
                                        f'label expects {"fire" if exp else "silent"}'))
        rows.append((c["id"], label, "fired" if fired else "silent", status))
        per_branch[branch][label] += 1

    print("=" * 74)
    print("STRUCTURAL HARNESS - per-case (mini-repo predicates)")
    print("=" * 74)
    for cid, label, fired, status in rows:
        flag = "" if status in ("OK", "n/a", "skip") else "  <<< MISMATCH"
        print(f"{cid:48} {fired:14} {status}{flag}")

    print("\n" + "=" * 74)
    print("PER-BRANCH CLASS BALANCE")
    print("=" * 74)
    print(f"{'branch':34} {'TP':>3} {'FP':>3} {'FN':>3} {'TN':>3}")
    for b in sorted(per_branch):
        pc = per_branch[b]
        print(f"{b:34} {pc['true_positive']:>3} {pc['false_positive']:>3} "
              f"{pc['false_negative']:>3} {pc['true_negative']:>3}")

    print("\n" + "=" * 74)
    if mismatches:
        print(f"RESULT: {len(mismatches)} MISMATCH(es):")
        for cid, why in mismatches:
            print(f"  - {cid}: {why}")
        return 1
    print("RESULT: all structural cases consistent with their predicates. [PASS]")
    return 0

if __name__ == "__main__":
    sys.exit(main())
