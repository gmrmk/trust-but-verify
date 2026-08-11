#!/usr/bin/env python3
"""
check_citations.py - citation-liveness gate (anti-AB-1, "citation theater").

WHY THIS EXISTS
---------------
references/grounding.md declares that every cited URL is "re-verifiable in CI"
and that "a release with stale citations MUST NOT ship". Until this script
existed, that was a promise with no mechanism - the exact failure the AB-1
defense is written to prevent. This is the mechanism.

WHAT IT DOES
------------
Reads every framework in `baseline_frameworks:` in trust-tree.yaml, fetches its
URL, and checks two things:

  1. LIVENESS (hard failure)  - the URL must not be GONE. A 404/410, or a
     connection that never completes, means the grounding a finding cites no
     longer exists.
  2. CONTENT MATCH (warning; hard failure under --strict) - a distinctive token
     from the framework's registered name must appear in the fetched body. A 200
     from a parked domain or a redirected marketing page is still a dead
     citation.

A 403 or 429 IS NOT STALENESS. It means the host refused *this client* - bot
protection, a WAF, or a corporate proxy - and says nothing about whether the
document exists. Both failure modes were observed while building this script:
ftc.gov serves 403 to a non-browser user-agent and 200 to a browser one, and a
sandboxed proxy returned 403 for github.com regardless of user-agent. Reporting
either as "stale citation" would be a false alarm, and a gate that cries wolf
gets ignored - which is the bypass normalization (AB-9) this whole repo refuses.
So blocked responses are reported as BLOCKED and need a human eye, not a red X.

Frameworks marked `external: false` are in-repo doctrine, not fetchable URLs;
they are checked as repo-relative paths instead.

WHY THIS IS NOT A PULL-REQUEST GATE
-----------------------------------
Standards bodies have outages. Wiring a network fetch into the PR gate means a
transient 503 from one government host blocks an unrelated merge, and the team
learns to click past a red check - which is bypass normalization (AB-9), the
thing the skill exists to refuse. So this runs on a schedule, on demand, and at
release, where a failure is actionable news instead of a merge blocker. The PR
gate stays hermetic: harnesses + branch schema + hook smoke tests.

USAGE:  python scripts/check_citations.py [--strict] [--timeout SECONDS]
EXIT:   0 if every URL is live (and, under --strict, content-matched); 1 otherwise.
"""
import argparse
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TREE = os.path.join(ROOT, "skills", "trust-but-verify", "trust-tree.yaml")

# Several standards hosts (ftc.gov among them) serve 403 to a non-browser
# user-agent and 200 to a browser one. Presenting as a browser is what makes the
# check measure the DOCUMENT rather than the bot policy in front of it.
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/126.0.0.0 Safari/537.36")
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Codes that prove the document is gone, versus codes that only prove the host
# refused us. Only the first group is a stale citation.
GONE = {404, 410}
BLOCKED = {401, 403, 405, 429}

# Words too generic to prove a page is the right page.
STOPWORDS = {
    "the", "and", "for", "list", "top", "series", "level", "sheet", "cheat",
    "guide", "practices", "authoring", "standard", "verification", "application",
    "security", "framework", "development", "software", "secure", "most",
    "dangerous", "weaknesses", "project", "controls", "license", "licenses",
}


def tokens(name):
    """Distinctive tokens from a framework's registered name."""
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9.\-]*", name)
    out = [w for w in words if w.lower() not in STOPWORDS and len(w) > 2]
    return out or words


def fetch(url, timeout, attempts=3):
    """Return (status, body_text). Retries transient failures with backoff."""
    ctx = ssl.create_default_context()
    last = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                return r.status, r.read().decode("utf-8", errors="ignore")
        except urllib.error.HTTPError as e:
            # A 4xx is a real answer, not a transient fault - do not retry.
            if 400 <= e.code < 500:
                return e.code, ""
            last = f"HTTP {e.code}"
        except Exception as e:  # timeout, DNS, TLS, connection reset
            last = type(e).__name__
        if i < attempts - 1:
            time.sleep(2 ** i)
    return None, f"unreachable ({last})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true",
                    help="treat a content-match miss as a failure (use at release)")
    ap.add_argument("--timeout", type=int, default=30)
    args = ap.parse_args()

    import yaml
    with open(TREE, "rb") as f:
        tree = yaml.safe_load(f)

    entries = []
    for cat, items in (tree.get("baseline_frameworks") or {}).items():
        for f in items or []:
            entries.append((cat, f))

    failures, warnings, blocked = [], [], []
    print("=" * 78)
    print("CITATION-LIVENESS GATE (anti-AB-1)")
    print("=" * 78)

    for cat, f in entries:
        fid, name, url = f.get("id"), f.get("name", ""), f.get("url", "")

        if f.get("external") is False:
            # In-repo doctrine: the "URL" is a repo-relative path.
            path = os.path.join(ROOT, url.split("#", 1)[0])
            ok = os.path.exists(path)
            print(f"  {'in-repo':>8}  {fid:26} {url}")
            if not ok:
                failures.append(f"{fid}: in-repo path does not exist: {url}")
            continue

        status, body = fetch(url, args.timeout)
        if status == 200:
            hits = [t for t in tokens(name) if t.lower() in body.lower()]
            mark = "match" if hits else "NO-MATCH"
            print(f"  {status:>8}  {fid:26} {mark:9} {url}")
            if not hits:
                msg = (f"{fid}: HTTP 200 but no token from {name!r} "
                       f"appears in the body - possible redirect or parked page")
                (failures if args.strict else warnings).append(msg)
        elif status in BLOCKED:
            print(f"  {status:>8}  {fid:26} {'BLOCKED':9} {url}")
            blocked.append(f"{fid}: {url} -> HTTP {status} (host refused this "
                           f"client; the document is NOT proven stale)")
        else:
            shown = status if status else "ERR"
            print(f"  {str(shown):>8}  {fid:26} {'':9} {url}")
            reason = f"HTTP {status}" if status else body
            if status in GONE or status is None:
                failures.append(f"{fid}: {url} -> {reason}")
            else:
                blocked.append(f"{fid}: {url} -> {reason} (unexpected status)")

    print()
    if blocked:
        print(f"BLOCKED ({len(blocked)}) - not counted as stale; open these in a "
              f"browser to confirm:")
        for b in blocked:
            print(f"  ? {b}")
        print()
    if warnings:
        print(f"CONTENT-MATCH WARNINGS ({len(warnings)}) - re-run with --strict to enforce:")
        for w in warnings:
            print(f"  ! {w}")
        print()

    if failures:
        print(f"RESULT: {len(failures)} stale citation(s):")
        for x in failures:
            print(f"  - {x}")
        print("\nA release with stale citations MUST NOT ship "
              "(references/grounding.md § Release-time verification).")
        return 1

    live = len(entries) - len(blocked)
    print(f"RESULT: {live} of {len(entries)} citations confirmed live"
          f"{' and content-matched' if args.strict else ''}"
          f"{f', {len(blocked)} blocked (unproven)' if blocked else ''}. [PASS]")
    print("Re-stamp `verified_accessible:` in references/grounding.md when this "
          "runs as part of a release.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
