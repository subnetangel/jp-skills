#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Structural checks for built PPTX files (PowerPoint itself is not needed, and not used).

  * every XML part parses; the file opens with python-pptx; slide count matches the HTML
  * clicks per slide == HTML build states - 1 (build 0 plays with the slide), from states.json
  * timing: cTn ids unique per slide, every spTgt / bldP target exists, bldP only on p:sp
  * presenter files carry speaker notes on every slide; share files have no notesSlide parts at all
  * docProps carry only neutral values (no author, company or last-modified-by other than the tool)
  * optional: your sensitivity config (see ../sensitivity_check.py) over every XML part of the share files

Usage: validate_pptx.py --states states.json [--sensitivity sensitivity.json] FILE.pptx [...]
A file whose name contains "-share" is checked as a share file. Exit 1 on any failure.
"""
import argparse
import collections
import json
import os
import re
import sys
import zipfile

from lxml import etree
from pptx import Presentation

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
NEUTRAL = "presentation-coach"


def check(path, steps, rules, allow):
    errs = []
    share = "-share" in os.path.basename(path)
    z = zipfile.ZipFile(path)
    for name in z.namelist():
        if name.endswith((".xml", ".rels")):
            try:
                etree.fromstring(z.read(name))
            except etree.XMLSyntaxError as e:
                errs.append(f"{name}: {e}")
    prs = Presentation(path)
    nslides = len(steps)
    if len(prs.slides) != nslides:
        errs.append(f"{len(prs.slides)} slides, HTML has {nslides}")
    clicks = []
    for n, s in enumerate(prs.slides, 1):
        el = s._element
        ids = {int(c.get("id")) for c in el.iter(P + "cNvPr")}
        sp_ids = {int(c.get("id")) for c in el.iter(P + "cNvPr") if c.getparent().getparent().tag == P + "sp"}
        ctn = [c.get("id") for c in el.iter(P + "cTn")]
        if len(ctn) != len(set(ctn)):
            errs.append(f"slide {n}: duplicate cTn ids")
        for t in el.iter(P + "spTgt"):
            if int(t.get("spid")) not in ids:
                errs.append(f"slide {n}: spTgt {t.get('spid')} missing")
        for b in el.iter(P + "bldP"):
            if int(b.get("spid")) not in sp_ids:
                errs.append(f"slide {n}: bldP {b.get('spid')} is not a p:sp")
        c = len(el.findall(f".//{P}cTn[@nodeType='clickEffect']"))
        want = max(steps.get(n, 1) - 1, 0)
        clicks.append(c)
        if c != want:
            errs.append(f"slide {n}: {c} clicks, HTML has {want}")
        has_notes = s.has_notes_slide and s.notes_slide.notes_text_frame.text.strip()
        if share and has_notes:
            errs.append(f"slide {n}: share file carries notes")
        if not share and not has_notes:
            errs.append(f"slide {n}: presenter file has no notes")
    if share and any("notesSlide" in nm for nm in z.namelist()):
        errs.append("share file has notesSlide parts")
    core = z.read("docProps/core.xml").decode("utf-8")
    for tag in ("dc:creator", "cp:lastModifiedBy"):
        m = re.search(rf"<{tag}>(.*?)</{tag}>", core)
        if m and m.group(1) not in ("", NEUTRAL):
            errs.append(f"docProps {tag} is {m.group(1)!r}")
    app = z.read("docProps/app.xml").decode("utf-8")
    if re.search(r"<(Company|Manager)>", app):
        errs.append("docProps/app.xml carries Company or Manager")
    if "docProps/thumbnail.jpeg" in z.namelist():
        errs.append("template thumbnail still present")
    if any(nm.startswith("ppt/printerSettings/") for nm in z.namelist()):
        errs.append("template printer settings still present")
    hits = {}
    if rules and share:
        text = "\n".join(z.read(nm).decode("utf-8", "ignore") for nm in z.namelist() if nm.endswith((".xml", ".rels")))
        for a in allow:
            text = a.sub("[allowed]", text)
        hits = {k: sorted({m.group(0) for m in rx.finditer(text)}) for k, rx in rules.items()}
        hits = {k: v for k, v in hits.items() if v}
        if hits:
            errs.append(f"sensitivity hits: {hits}")
    print(f"{os.path.basename(path)}: {os.path.getsize(path):,} bytes, {len(prs.slides)} slides, clicks per slide {clicks}, "
          f"notes {'none' if share else 'on every slide' if not any('no notes' in e for e in errs) else 'MISSING'}"
          + (f", sensitivity {'clean' if not hits else 'FAIL'}" if rules and share else ""))
    return errs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--states", required=True)
    ap.add_argument("--sensitivity")
    ap.add_argument("files", nargs="+")
    a = ap.parse_args()
    steps = collections.Counter(s[0] for s in json.load(open(a.states)))
    rules, allow = ({}, [])
    if a.sensitivity:
        from sensitivity_check import load
        rules, allow = load(a.sensitivity)
    rc = 0
    for f in a.files:
        for e in check(f, steps, rules, allow):
            print("  FAIL:", e); rc = 1
    print("HTML build states per slide:", [steps[n] for n in sorted(steps)], "-> clicks", [max(steps[n] - 1, 0) for n in sorted(steps)])
    return rc


if __name__ == "__main__":
    sys.exit(main())
