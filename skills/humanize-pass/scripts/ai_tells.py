#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""List likely AI-writing tells in prose files, by line, so a person can rewrite them.

Usage:
  ai_tells.py FILE [FILE ...] [--max N] [--json OUT.json]

Reads markdown, text, HTML and JSON as text (HTML tags, <style> and <script> blocks, and fenced code blocks in
markdown are skipped). Prints  file:line  [pattern]  match  and ends with  TELLS: N  (and a count per pattern).
A hit is a prompt to look closer, not proof; the pattern numbers match SKILL.md. Exit 0, or 1 when --max is given
and the count is above it. Python 3.9+, standard library only.
"""
import argparse
import json
import re
import sys

W = r"\b"
PATTERNS = [
    (1, "not X but Y", re.compile(r"\b(?:it's|it is|this is|that's|they're)\s+not\s+(?:just\s+)?(?:a|an|the|about)?\s*[\w-]+(?:\s[\w-]+)?[,;]\s*(?:it's|it is|but|they're)\b", re.I)),
    (1, "not only X but", re.compile(r"\bnot (?:just|only|merely)\b[^.]{1,60}\bbut\b", re.I)),
    (2, "one-line closer", re.compile(r"(?:^|[.!?]\s+)(?:That's|This is|Here's) (?:the )?(?:real |whole |big )?(?:win|point|magic|difference|key|game[- ]changer)[.!]", re.I)),
    (2, "fragment pair", re.compile(r"(?:^|[.!?]\s+)No [a-z]+\. No [a-z]+\.", re.I)),
    (3, "staged reveal", re.compile(r"\b(?:here's the (?:kicker|thing|catch|twist)|the result\?|so what does this mean\??|the best part\?|guess what)", re.I)),
    (5, "dash connector", re.compile(r"\s[\u2014\u2013]\s|\w\u2014\w|\s--\s")),
    (6, "hype word", re.compile(W + r"(?:seamless(?:ly)?|robust|leverag(?:e|es|ed|ing)|unlock(?:s|ed|ing)?|empower(?:s|ed|ing)?|elevat(?:e|es|ed|ing)|effortless(?:ly)?|supercharg(?:e|es|ed|ing)|delv(?:e|es|ing)|pivotal|crucial|landscape|tapestry|testament|underscor(?:e|es|ed|ing)|foster(?:s|ed|ing)?|showcas(?:e|es|ed|ing)|game[- ]changer|world[- ]class|next[- ]generation|cutting[- ]edge|revolutioni[sz](?:e|es|ed|ing))" + W, re.I)),
    (7, "inflated significance", re.compile(r"\b(?:marks? a (?:pivotal|significant|major) (?:shift|moment|milestone)|sets? the stage for|paves? the way for|in a new era)\b", re.I)),
    (8, "borrowed authority", re.compile(r"\b(?:experts (?:agree|say)|studies (?:show|suggest)|industry reports?|research shows|it is widely (?:known|accepted))\b", re.I)),
    (9, "copula dodge", re.compile(r"\b(?:serves as|stands as|acts as a testament|boasts)\b", re.I)),
    (10, "-ing tail", re.compile(r",\s(?:highlighting|underscoring|showcasing|reflecting|demonstrating|emphasizing|ensuring)\s(?:our|the|its|their|a)\b", re.I)),
    (11, "filler opener", re.compile(r"\b(?:in today's (?:fast-paced|digital|ever-changing)|let's dive in|let's delve|without further ado|i hope this helps|great question|here's what you need to know|in conclusion,)", re.I)),
    (12, "stacked hedge", re.compile(r"\b(?:could|might|may) (?:potentially|possibly|perhaps)\b|\bpotentially (?:could|might|may)\b", re.I)),
]
FENCE = re.compile(r"^\s*```")
TAG = re.compile(r"<[^>]+>")
BLOCK = re.compile(r"<(style|script)\b[^>]*>.*?</\1>", re.S | re.I)


def prose_lines(path, text):
    if path.endswith((".html", ".htm")):
        text = BLOCK.sub(lambda m: "\n" * m.group(0).count("\n"), text)
        text = TAG.sub(" ", text)
    in_code = False
    for n, line in enumerate(text.splitlines(), 1):
        if path.endswith(".md") and FENCE.match(line):
            in_code = not in_code
            continue
        if in_code:
            continue
        if path.endswith(".md"):
            line = re.sub(r"`[^`]*`", " ", line)
        yield n, line


def scan(path):
    text = open(path, encoding="utf-8", errors="replace").read()
    hits = []
    for n, line in prose_lines(path, text):
        for num, name, rx in PATTERNS:
            for m in rx.finditer(line):
                hits.append({"file": path, "line": n, "pattern": num, "name": name, "match": m.group(0).strip()[:80]})
    return hits


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--max", type=int)
    ap.add_argument("--json")
    a = ap.parse_args()
    hits = [h for f in a.files for h in scan(f)]
    for h in hits:
        print(f"{h['file']}:{h['line']}  [{h['pattern']} {h['name']}]  {h['match']}")
    per = {}
    for h in hits:
        per[h["name"]] = per.get(h["name"], 0) + 1
    print(f"TELLS: {len(hits)}" + (" (" + ", ".join(f"{k} {v}" for k, v in sorted(per.items())) + ")" if per else ""))
    if a.json:
        json.dump(hits, open(a.json, "w", encoding="utf-8"), indent=1)
    return 1 if a.max is not None and len(hits) > a.max else 0


if __name__ == "__main__":
    sys.exit(main())
