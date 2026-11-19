#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Every printed PDF (staff quick-start, booth card) embeds only the faces you ship. Fails on any other face, on a
Type3 font (what Chrome draws when no installed face has the glyph, e.g. a check mark or an arrow) and on a PDF with no
font at all. This catches the 'card printed in a fallback serif' failure before a person sees the paper.

    pdf_fonts_check.py --allow BrandSans-Regular,BrandSans-Bold,DejaVuSans FILE.pdf [...]

--allow takes /BaseFont names without the subset prefix (ABCDEF+). Run it once on a PDF you know is right to read
the names. shortcut: reads the font dictionaries as plain text, which is how Chrome's print-to-PDF writes them; a PDF
that packs its objects into compressed object streams reads as 'no fonts' and fails loudly rather than passing.
"""
import argparse
import re
import sys


def fonts(path):
    b = open(path, "rb").read()
    names = sorted({m.decode().split("+", 1)[-1] for m in re.findall(rb"/BaseFont\s*/([A-Za-z0-9+_.-]+)", b)})
    return names, len(re.findall(rb"/Subtype\s*/Type3", b))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--allow", required=True, help="comma-separated face names")
    ap.add_argument("pdfs", nargs="+")
    a = ap.parse_args()
    allow = {x.strip() for x in a.allow.split(",") if x.strip()}
    bad = 0
    for p in a.pdfs:
        names, t3 = fonts(p)
        other = [n for n in names if n not in allow]
        ok = bool(names) and not other and not t3
        bad += not ok
        print(f"{'PASS' if ok else 'FAIL'} {p.split('/')[-1]}: {', '.join(names) or 'no fonts'}"
              + (f"; not allowed: {', '.join(other)}" if other else "") + (f"; {t3} Type3 fonts" if t3 else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
