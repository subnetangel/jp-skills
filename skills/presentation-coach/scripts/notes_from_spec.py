#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Write a deck's speaker notes (its NOTES block) from the talk-track spec.

Usage:
  notes_from_spec.py SPEC.json DECK.html [--wpm 120]

One spec, two outputs: build_talk_track.py renders the rehearsal page from SPEC.json, and this script
rewrites the  /* NOTES:BEGIN */ ... /* NOTES:END */  block in DECK.html from the same file, so the
notes behind N in the deck and the page you rehearse from cannot drift apart. Run build.py afterwards.

Mapping (one entry per segment, in order; the spec needs one segment per <section class="slide">):
  title + estimate          -> <h2>
  checkpoint, purpose       -> <p class="cue">
  script text               -> <p> (anchor paragraphs get class="anchor"); [cue] -> <em>[cue]</em>, **x** -> <b>x</b>
  script proposal           -> <p class="cue">label: proposal</p>
  transition                -> <p class="cue">Transition out: ...</p>
  notes                     -> <div class="confirm"> list
  cue_card                  -> extra block on the first slide
  questions                 -> extra block on the last slide
Word counts reuse build_talk_track.spoken_words, so the estimates match the page.
"""
import argparse
import html
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build_talk_track import spoken_words  # noqa: E402

CHIP = re.compile(r"\[(pause|slow|soft|click|point|move|act|room)(?::\s*([^\]]*))?\]")
BOLD = re.compile(r"\*\*(.+?)\*\*")
LABEL = {"click": "\u2192 {d}", "point": "point {d}", "move": "{d}", "act": "{d}",
         "pause": "pause{c}{d}", "slow": "slow{c}{d}", "soft": "softer{c}{d}", "room": "ask the room{c}{d}"}


def inline(text: str) -> str:
    out = html.escape(text, quote=False)

    def chip(m):
        kind, detail = m.group(1), (m.group(2) or "").strip()
        label = LABEL[kind].format(d=detail, c=": " if detail else "")
        return f"<em>[{label.strip()}]</em>"

    return BOLD.sub(r"<b>\1</b>", CHIP.sub(chip, out))


def mmss(seconds: float) -> str:
    s = int(round(seconds))
    return f"{s // 60}:{s % 60:02d}"


def block(title: str, items: list) -> str:
    return f"<div class=\"confirm\"><h3>{title}</h3><ul>{''.join(items)}</ul></div>"


def segment_html(seg: dict, est: float, extra: list) -> str:
    parts = [f"<h2>{inline(seg['title'])} \u00b7 ~{mmss(est)} (estimate)</h2>"]
    if seg.get("checkpoint"):
        parts.append(f"<p class=\"cue\">Checkpoint: {inline(seg['checkpoint'])}</p>")
    if seg.get("purpose"):
        parts.append(f"<p class=\"cue\">Purpose: {inline(seg['purpose'])}</p>")
    for p in seg.get("script", []):
        if "proposal" in p:
            parts.append(f"<p class=\"cue\">{inline(p.get('label', 'Proposed, accept or reject'))}: {inline(p['proposal'])}</p>")
        else:
            cls = " class=\"anchor\"" if p.get("anchor") else ""
            parts.append(f"<p{cls}>{inline(p['text'])}</p>")
    if seg.get("transition"):
        parts.append(f"<p class=\"cue\">Transition out: {inline(seg['transition'])}</p>")
    if seg.get("notes"):
        parts.append(block(inline(seg.get("notes_title", "Notes and flags")), [f"<li>{inline(n)}</li>" for n in seg["notes"]]))
    return "\n     ".join(parts + extra)


def cue_card(cc: dict) -> str:
    items = []
    if cc.get("message"):
        items.append(f"<li><b>Message:</b> {inline(cc['message'])}</li>")
    for a in cc.get("anchors", []):
        items.append(f"<li><b>{inline(a.get('label', ''))}</b> {inline(a.get('text', ''))}</li>" if isinstance(a, dict) else f"<li>{inline(a)}</li>")
    if cc.get("ask"):
        items.append(f"<li><b>Ask:</b> {inline(cc['ask'])}</li>")
    if cc.get("reminders"):
        items.append(f"<li>{inline(cc['reminders'])}</li>")
    return block("Cue card", items)


def questions(qs: list) -> str:
    warn = "\u26a0 "
    return block("Likely questions", [f"<li><b>{warn if q.get('confirm') else ''}{inline(q['q'])}</b> {inline(q['a'])}</li>" for q in qs])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("deck")
    ap.add_argument("--wpm", type=float, default=120)
    a = ap.parse_args()
    spec = json.loads(pathlib.Path(a.spec).read_text(encoding="utf-8"))
    deck = pathlib.Path(a.deck)
    src = deck.read_text(encoding="utf-8")
    segs = spec["segments"]
    total = len(re.findall(r'<section class="slide[ "]', src))
    if len(segs) != total:
        print(f"spec has {len(segs)} segments but the deck has {total} slides", file=sys.stderr)
        return 1

    entries, cum = [], 0.0
    for i, seg in enumerate(segs):
        words = sum(spoken_words(p["text"]) for p in seg.get("script", []) if "text" in p)
        if seg.get("transition") and seg.get("count_transition", True):
            words += spoken_words(seg["transition"])
        est = words / a.wpm * 60 + float(seg.get("pauses_s", 0))
        cum += est
        extra = []
        if i == 0 and spec.get("cue_card"):
            extra.append(cue_card(spec["cue_card"]))
        if i == len(segs) - 1 and spec.get("questions"):
            extra.append(questions(spec["questions"]))
        entry = segment_html(seg, est, extra)
        if "`" in entry or "${" in entry:
            print(f"segment {i + 1}: a backtick or ${{ would break the JS template literal", file=sys.stderr)
            return 1
        entries.append(entry)
        print(f"slide {i + 1}: {words} words, ~{mmss(est)}, cumulative ~{mmss(cum)}")

    new_block = ("/* NOTES:BEGIN */\n  const NOTES = [\n"
                 + ",\n".join("    `" + e + "`" for e in entries)
                 + "\n  ];\n  /* NOTES:END */")
    new, n = re.subn(r"/\* NOTES:BEGIN \*/.*?/\* NOTES:END \*/", lambda m: new_block, src, count=1, flags=re.S)
    if n != 1:
        print("NOTES markers not found in the deck", file=sys.stderr)
        return 1
    deck.write_text(new, encoding="utf-8")
    print(f"NOTES written from {a.spec}: {len(entries)} slides, ~{mmss(cum)} total (estimate, {a.wpm:g} wpm)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
