#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Find the source line of each phrase in a demo file, so every cheat-sheet fact can cite file:line.

Usage: python3 where.py FILE 'phrase one' 'phrase two' ...
Prints L<line>[,<line>...] | phrase, or MISSING | phrase. Tags and entities are ignored; attribute text is found in the raw lines.
"""
import html
import re
import sys

if len(sys.argv) < 3:
    sys.exit(__doc__)
path, phrases = sys.argv[1], sys.argv[2:]
lines = open(path, encoding='utf-8', errors='replace').read().split('\n')
norm = [re.sub(r'\s+', ' ', html.unescape(re.sub(r'\\u003c[^>]*>|<[^>]+>', '', l.replace("\\'", "'")))) for l in lines]
missing = 0
for ph in phrases:
    hits = [i + 1 for i, l in enumerate(norm) if ph in l] or [i + 1 for i, l in enumerate(lines) if ph in l]  # raw lines catch attribute text (aria-label, title)
    missing += not hits
    print(f"L{','.join(map(str, hits[:4]))}" if hits else 'MISSING', '|', ph)
sys.exit(1 if missing else 0)
