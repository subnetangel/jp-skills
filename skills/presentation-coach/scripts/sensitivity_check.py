#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Refuse to share a file that carries terms you said must never leave the room.

Usage:
  sensitivity_check.py --config sensitivity.json FILE [FILE ...] [--warn-only PATTERN]

Every forbidden term and pattern comes from YOUR config; nothing is hard-coded. Config (JSON):

  {
    "terms":    {"codenames": ["Project Bluebird"], "other-clients": ["Globex"]},
    "patterns": {"long-ids": "(?<![\\\\d.])\\\\d{12}(?![\\\\d.])", "money": "\\\\$\\\\s?\\\\d"},
    "allow":    ["Bluebird Lane"],
    "ignore_case": true
  }

  terms     groups of literal words or phrases, matched as whole words
  patterns  groups of regular expressions (Python syntax)
  allow     phrases blanked out before scanning (a legitimate phrase that contains a term)

Base64 data URIs are blanked before scanning so embedded images and fonts cannot cause noise.
Exit 1 if any hit is found in a file that is not covered by --warn-only (a substring of the file
name, e.g. --warn-only presenter); those files are reported but do not fail. Exit 2 on a bad config.
Python 3.9+, standard library only.
"""
import argparse
import json
import pathlib
import re
import sys

DATA_URI = re.compile(r"data:[a-z0-9.+/-]+;base64,[A-Za-z0-9+/=]+", re.I)


def load(path: str):
    try:
        cfg = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"bad config {path}: {e}", file=sys.stderr)
        sys.exit(2)
    flags = re.I if cfg.get("ignore_case", True) else 0
    rules = {}
    for group, words in cfg.get("terms", {}).items():
        alts = "|".join(re.escape(w) for w in words if w.strip())
        if alts:
            rules[group] = re.compile(rf"(?<![\w-])(?:{alts})(?![\w-])", flags)
    for group, pat in cfg.get("patterns", {}).items():
        try:
            rules[group] = re.compile(pat, flags)
        except re.error as e:
            print(f"bad pattern {group!r}: {e}", file=sys.stderr)
            sys.exit(2)
    allow = [re.compile(re.escape(p), flags) for p in cfg.get("allow", []) if p.strip()]
    if not rules:
        print("config has no terms or patterns; nothing to check", file=sys.stderr)
        sys.exit(2)
    return rules, allow


def scan(text: str, rules: dict, allow: list) -> dict:
    text = DATA_URI.sub("data:…", text)
    for a in allow:
        text = a.sub("[allowed]", text)
    hits = {}
    for group, rx in rules.items():
        found = [m.group(0) for m in rx.finditer(text)]
        if found:
            hits[group] = found
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("--warn-only", action="append", default=[], help="file-name substring whose hits only warn")
    ap.add_argument("files", nargs="+")
    a = ap.parse_args()
    rules, allow = load(a.config)
    rc = 0
    for f in a.files:
        p = pathlib.Path(f)
        hits = scan(p.read_text(encoding="utf-8", errors="replace"), rules, allow)
        warn = any(w in p.name for w in a.warn_only)
        if not hits:
            print(f"clean: {p}")
            continue
        print(f"{'WARN' if warn else 'FAIL'}: {p}")
        for group, found in hits.items():
            print(f"  {group}: {len(found)} hit(s): {sorted(set(found))[:8]}")
        if not warn:
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
