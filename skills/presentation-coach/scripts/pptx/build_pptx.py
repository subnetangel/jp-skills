#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Native PowerPoint from a deck made from assets/deck-template.html: dark and light, presenter and share.

Usage:
  build_pptx.py DECK.html --spec talk-track-spec.json --out dist/ [--name NAME] [--states-override FILE]
                [--themes dark,light] [--font-sans Arial] [--font-mono Consolas] [--sensitivity sensitivity.json]
                [--preview] [--work DIR]

DECK.html may be the source (with the {{notes_enabled}} placeholder; it is built first with ../build.py) or a built
presenter file. Writes OUT/NAME-dark.pptx, OUT/NAME-light.pptx (speaker notes from the spec) and
OUT/NAME-share-dark.pptx, OUT/NAME-share-light.pptx (no notes parts at all), then validates all four.

Steps
  1. Build states from the deck's own markup: one state per build step of every slide (data-len on each
     <section class="slide">, at least one per slide), written to WORK/states.json. --states-override takes a JSON
     object {"3": 5} (slide -> number of states) or a full list [[slide, "sN-bK", label, k], ...].
  2. dom_extract.js (Node + Playwright Chromium) walks every state in each theme and records native drawing
     instructions plus a reference still.
  3. pptx_native.py turns the records into real shapes, text and timing (see its docstring for the animation map).
  4. validate_pptx.py checks XML, clicks per slide against the HTML, notes only in presenter files, neutral
     docProps, and (with --sensitivity) your forbidden terms in the share files.
  5. --preview renders every click state from the PPTX (native_preview.py) and compares it with the HTML still.

Dependencies: Node 18+ with Playwright and its Chromium (npm i -D playwright && npx playwright install chromium, or
set PLAYWRIGHT_PATH to an installed playwright module); Python 3.9+ with python-pptx, lxml and Pillow
(pip install python-pptx lxml pillow); numpy for --preview (pip install numpy); fontconfig's fc-match for --preview fonts.
"""
import argparse
import importlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parent

INSTALL = {
    "pptx": "pip install python-pptx", "lxml": "pip install lxml", "PIL": "pip install pillow", "numpy": "pip install numpy",
}


def check_deps(preview: bool) -> None:
    missing = []
    for mod in ("pptx", "lxml", "PIL") + (("numpy",) if preview else ()):
        try:
            importlib.import_module(mod)
        except ImportError:
            missing.append(f"Python module '{mod}': {INSTALL[mod]}")
    node = shutil.which("node")
    if not node:
        missing.append("Node.js 18+ (https://nodejs.org), then: npm i -D playwright && npx playwright install chromium")
    else:
        probe = ("const t=[process.env.PLAYWRIGHT_PATH,'playwright'].filter(Boolean);let pw=null;"
                 "for(const x of t){try{pw=require(x);break}catch(e){}}"
                 "if(!pw){console.log('NO_PLAYWRIGHT');process.exit(0)}"
                 "const p=pw.chromium.executablePath();console.log(require('fs').existsSync(p)?'OK':'NO_CHROMIUM')")
        r = subprocess.run([node, "-e", probe], capture_output=True, text=True, cwd=os.getcwd())
        out = r.stdout.strip()
        if out == "NO_PLAYWRIGHT":
            missing.append("Playwright for Node: npm i -D playwright  (or set PLAYWRIGHT_PATH to an installed playwright module)")
        elif out == "NO_CHROMIUM":
            missing.append("Playwright's Chromium: npx playwright install chromium")
        elif out != "OK":
            missing.append(f"could not probe Playwright: {r.stderr.strip()[:200]}")
    if preview and not shutil.which("fc-match"):
        print("note: fc-match not found; previews fall back to DejaVu Sans", file=sys.stderr)
    if missing:
        print("missing dependencies:", *missing, sep="\n  ", file=sys.stderr)
        sys.exit(3)


def derive_states(html, override_path):
    sections = re.findall(r"<section\b[^>]*\bclass=\"slide\b[^\"]*\"[^>]*>", html)
    if not sections:
        sys.exit("no <section class=\"slide\"> elements found; is this a deck made from assets/deck-template.html?")
    lens = {}
    for n, tag in enumerate(sections, 1):
        m = re.search(r'\bdata-len="(\d+)"', tag)
        lens[n] = max(1, int(m.group(1)) if m else 0)
    if override_path:
        ov = json.load(open(override_path))
        if isinstance(ov, list):
            return ov
        for k, v in ov.items():
            lens[int(k)] = max(1, int(v))
    return [[n, f"s{n}-b{k}", f"slide {n} build {k + 1} of {lens[n]}", k] for n in sorted(lens) for k in range(lens[n])]


def notes_from_spec(spec: dict, nslides: int):
    segs = spec.get("segments", [])
    if len(segs) != nslides:
        sys.exit(f"spec has {len(segs)} segments but the deck has {nslides} slides")
    clean = lambda s: re.sub(r"\*\*(.+?)\*\*", r"\1", s)   # noqa: E731
    out = []
    for i, seg in enumerate(segs):
        lines = [clean(seg.get("title", f"Slide {i + 1}"))]
        if seg.get("checkpoint"):
            lines.append("Checkpoint: " + clean(seg["checkpoint"]))
        if seg.get("purpose"):
            lines.append("Purpose: " + clean(seg["purpose"]))
        lines.append("")
        for p in seg.get("script", []):
            if "proposal" in p:
                lines.append(f"{p.get('label', 'Proposed, accept or reject')}: {clean(p['proposal'])}")
            else:
                lines.append(("ANCHOR: " if p.get("anchor") else "") + clean(p["text"]))
            lines.append("")
        if seg.get("transition"):
            lines.append("Transition: " + clean(seg["transition"]))
        for note in seg.get("notes", []):
            lines.append("• " + clean(note))
        if i == 0 and spec.get("cue_card"):
            cc = spec["cue_card"]; lines += ["", "CUE CARD", "Message: " + clean(cc.get("message", ""))]
            for a in cc.get("anchors", []):
                lines.append("• " + (clean(f"{a.get('label', '')} {a.get('text', '')}") if isinstance(a, dict) else clean(a)))
            if cc.get("ask"):
                lines.append("Ask: " + clean(cc["ask"]))
        if i == nslides - 1 and spec.get("questions"):
            lines += ["", "LIKELY QUESTIONS"]
            for q in spec["questions"]:
                lines.append(("⚠ " if q.get("confirm") else "") + clean(q["q"]) + " " + clean(q["a"]))
        out.append("\n".join(lines).strip())
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    ap.add_argument("--spec", required=True, help="talk-track spec; its segments become the presenter notes")
    ap.add_argument("--out", default="dist")
    ap.add_argument("--name")
    ap.add_argument("--states-override")
    ap.add_argument("--themes", default="dark,light")
    ap.add_argument("--font-sans", default="Arial")
    ap.add_argument("--font-mono", default="Consolas")
    ap.add_argument("--sensitivity")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--work", help="working folder for extraction records and previews (default OUT/.pptx-work)")
    a = ap.parse_args()
    check_deps(a.preview)

    deck = pathlib.Path(a.deck).resolve()
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    work = pathlib.Path(a.work or out / ".pptx-work").resolve(); work.mkdir(parents=True, exist_ok=True)
    name = a.name or deck.stem
    html = deck.read_text(encoding="utf-8")
    if "{{notes_enabled}}" in html:   # a source deck: build the presenter copy first
        subprocess.run([sys.executable, str(SCRIPTS / "build.py"), str(deck), "--out-dir", str(work), "--name", "deck"], check=True)
        deck = work / "deck.html"; html = deck.read_text(encoding="utf-8")
    title = (re.search(r"<title>(.*?)</title>", html, re.S) or [None, name])[1].strip()

    states = derive_states(html, a.states_override)
    (work / "states.json").write_text(json.dumps(states, indent=1))
    nslides = len({s[0] for s in states})
    notes = notes_from_spec(json.loads(pathlib.Path(a.spec).read_text(encoding="utf-8")), nslides)
    per_slide = [sum(1 for s in states if s[0] == n) for n in sorted({s[0] for s in states})]
    print(f"{nslides} slides, build states per slide {per_slide}")

    sys.path.insert(0, str(HERE))
    import pptx_native
    pptx_native.FONTS.update({"sans": a.font_sans, "mono": a.font_mono})
    built = []
    for theme in [t.strip() for t in a.themes.split(",") if t.strip()]:
        folder = work / theme
        subprocess.run(["node", str(HERE / "dom_extract.js"), str(work / "states.json"), str(deck), str(folder), theme], check=True)
        for with_notes, label in ((True, ""), (False, "share-")):
            path = out / f"{name}-{label}{theme}.pptx"
            rep = pptx_native.build(str(folder), states, notes if with_notes else None, str(path), title)
            built.append((path, theme))
            print(path, f"{path.stat().st_size:,} bytes", "clicks per slide", [rep[n]["clicks"] for n in sorted(rep)])

    cmd = [sys.executable, str(HERE / "validate_pptx.py"), "--states", str(work / "states.json")]
    if a.sensitivity:
        cmd += ["--sensitivity", a.sensitivity]
    rc = subprocess.run(cmd + [str(p) for p, _ in built]).returncode

    if a.preview:
        import native_preview
        for path, theme in built:
            if "-share-" in path.name:
                continue   # the share file has the same slides as the presenter file
            rows = native_preview.compare(str(path), str(work / "preview" / theme), str(work / theme / "stills"))
            worst = sorted(rows, key=lambda r: -r[1])[:3]
            print(f"preview {theme}: {len(rows)} states, mean |diff| vs HTML {sum(d for _, d in rows) / max(len(rows), 1):.2f}, "
                  f"worst {', '.join(f'{s} {d:.2f}' for s, d in worst)}; sheets in {work / 'preview' / theme}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
