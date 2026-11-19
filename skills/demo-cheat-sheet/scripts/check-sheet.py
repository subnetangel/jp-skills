#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check a booth cheat sheet before it ships.

Usage: python3 check-sheet.py SHEET.md [--deny-file TERMS.txt] [--allow-id NUMBER ...]
Fails (exit 1) on: a missing required section, a dollar figure, a 12-digit number not listed with --allow-id (for
example a documentation placeholder you chose to show), more than 750 words (one printed page), or a term from
--deny-file (one term per line, e.g. codenames). Prints one line per problem.
"""
import argparse
import re
import sys

REQUIRED = ['What it is', 'What the product delivers', '30-second pitch', 'How to drive it',
            'Three key points', 'Likely questions', 'What not to claim', 'Offline and kiosk notes']

ap = argparse.ArgumentParser()
ap.add_argument('sheet')
ap.add_argument('--deny-file', help='file with one forbidden term per line (codenames, customer names)')
ap.add_argument('--allow-id', action='append', default=[], help='a 12-digit number that may appear; repeatable')
a = ap.parse_args()
text = open(a.sheet, encoding='utf-8').read()
problems = []
heads = [h.lower() for h in re.findall(r'^##\s+(.+)$', text, re.M)]
for r in REQUIRED:
    if not any(h.startswith(r.lower()) for h in heads):
        problems.append(f'missing section: {r}')
for m in re.finditer(r'(?<![\w])\$\s?\d[\d,.]*\s*[kKmMbB]?', text):
    problems.append(f'dollar figure: {m.group(0).strip()}')
for m in re.finditer(r'(?<!\d)\d{12}(?!\d)', text):
    if m.group(0) not in set(a.allow_id):
        problems.append(f'12-digit number (an identifier?): {m.group(0)[:4]}…')
words = len(re.findall(r'\S+', text))
if words > 750:
    problems.append(f'{words} words: over one page (750)')
if a.deny_file:
    for term in filter(None, (t.strip() for t in open(a.deny_file, encoding='utf-8'))):
        if re.search(r'(?<!\w)' + re.escape(term) + r'(?!\w)', text, re.I):  # whole words: a short term like "PAR" must not hit "parallel"
            problems.append(f'denied term: {term}')
for p in problems:
    print('FAIL', p)
print(f'{"PASS" if not problems else "FAIL"} {a.sheet} ({words} words)')
sys.exit(1 if problems else 0)
