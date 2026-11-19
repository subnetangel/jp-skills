#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Sensitivity scan of a demo cut, a data file or a built HTML. FAIL (exit 1) on anything that must not ship.

    scan_cut.py PATH [PATH ...] --deny deny.json [--json SCAN.json]

Fails on:
  - a 12-digit number (not inside a hex digest) that is not in the allow list (default: empty)
  - a cloud access-key id of the AKIA/ASIA shape
  - any pattern in deny.json: {"allow_ids": [...], "deny": {"rule-name": "regex", ...}}
    Put your codenames, real identifiers and fragments of them, resource-name patterns of your platform, fixture
    prefixes, aliases and internal hostnames there, case-insensitive, including fragments a TUI cuts at a line wrap.
    Keep deny.json out of the shipped package. (The older key "allow_accounts" still works.)
Terminal streams (*.io) are scanned after removing ANSI/OSC escape sequences, so a name split by escapes is still seen.
Binary files are skipped and listed, because a person must look at those.
"""
import argparse
import json
import os
import re
import sys

ANSI = re.compile(r"\x1b\[[0-9;?<>=]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b[()][A-Za-z0-9]")
BINARY = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".mp4", ".webm", ".pdf", ".woff", ".woff2", ".zip"}


def files(paths):
    for p in paths:
        if os.path.isdir(p):
            for d, _, fs in os.walk(p):
                for f in fs:
                    yield os.path.join(d, f)
        else:
            yield p


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--deny", required=True)
    ap.add_argument("--json")
    a = ap.parse_args()
    cfg = json.load(open(a.deny))
    allow = set(cfg.get("allow_ids", cfg.get("allow_accounts", []))) | {"0" * 12}   # the redactor's placeholder
    rules = {
        "long-id-not-allowed": re.compile(r"(?<![\dA-Fa-f.])\d{12}(?![\dA-Fa-f.])"),
        "access-key-id": re.compile(r"\b(?!AKIAEXAMPLE)(AKIA|ASIA)[A-Z0-9]{16}\b"),
        **{k: re.compile(v, re.I) for k, v in cfg.get("deny", {}).items()},
    }
    fails, skipped, n = {}, [], 0
    for p in files(a.paths):
        if os.path.splitext(p)[1].lower() in BINARY:
            skipped.append(p)
            continue
        if os.path.basename(p) in ("SCAN.json",) or os.path.abspath(p) == os.path.abspath(a.deny):
            continue
        t = open(p, "rb").read().decode("utf-8", "replace")
        if p.endswith(".io"):
            t = ANSI.sub("", t)
        n += 1
        for k, pat in rules.items():
            hits = set()
            for m in pat.finditer(t):
                if k == "long-id-not-allowed" and m.group(0) in allow:
                    continue
                hits.add(m.group(0))
            if hits:
                fails.setdefault(p, {})[k] = sorted(hits)[:8]
    res = {"verdict": "fail" if fails else "pass", "filesScanned": n, "allowIds": sorted(allow),
           "fails": fails, "binarySkipped": skipped}
    if a.json:
        json.dump(res, open(a.json, "w"), indent=1)
    print(json.dumps({k: res[k] for k in ("verdict", "filesScanned")} | {"failFiles": len(fails),
                     "binarySkipped": len(skipped)}, indent=1))
    for p, r in fails.items():
        print(f"FAIL {p}: {r}", file=sys.stderr)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
