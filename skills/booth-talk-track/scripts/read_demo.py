#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Read an existing demo (a local HTML file or a URL) and write an inventory to write a booth spec from.

Usage:
  read_demo.py DEMO OUTDIR [--query "?idle=0"] [--viewport 1688x1130] [--theme dark|light] [--key ArrowRight]
               [--max 60] [--settle 1.2] [--forbid "a,b"]

What it does (offline; nothing is clicked except the advance key):
  * Opens the demo in headless Chromium and walks it with the advance key (default ArrowRight) until five presses
    in a row change nothing, or --max presses.
  * For every distinct screen: a screenshot, the visible headings, the visible button and link labels, and the
    visible text, so the spec can quote exact labels and on-screen claims.
  * Lists every landmark the file declares up front (section aria-labels, slide ids), hidden ones included, and
    whether the file holds hidden notes or panels (text in the DOM that is not visible): staff-only text there is
    still visible to anyone with developer tools.
  * Reports whether the demo is built on the demo-engine template (the shared screen modes), so the talk track can use
    the template's words for the staff panel, modes and keys, or describe the demo's own controls where it differs.
  * Scans the visible text for --forbid terms, 12-digit numbers, dollar amounts and dates.
Writes OUTDIR/inventory.md, OUTDIR/inventory.json and OUTDIR/screen-NN.png. It cannot know what a click does: every
click path in the talk track still has to be driven once, or marked "verify in the drill".
Needs the Python Playwright package with Chromium.
"""
import argparse
import hashlib
import json
import os
import re
import sys

JS_STATE = """() => {
  const vis = e => { const r = e.getBoundingClientRect(), s = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && r.bottom > 0 && r.right > 0 && r.top < innerHeight && r.left < innerWidth
      && s.visibility !== 'hidden' && s.display !== 'none' && +s.opacity !== 0; };
  const txt = e => (e.innerText || e.getAttribute('aria-label') || '').trim().replace(/\\s+/g, ' ');
  const pick = sel => [...document.querySelectorAll(sel)].filter(vis).map(txt).filter(Boolean);
  return { headings: pick('h1,h2,h3'), controls: [...new Set(pick('button,[role=button],[role=tab],a[href],select,input[type=button]'))],
           text: document.body.innerText.replace(/\\n{3,}/g, '\\n\\n').trim(),
           shown: [...document.querySelectorAll('body *')].filter(e => !e.children.length && vis(e)).map(txt).filter(Boolean).join('|'),
           where: location.hash };
}"""

JS_LANDMARKS = """() => ({
  sections: [...document.querySelectorAll('section[aria-label], [role=region][aria-label], [data-slide]')]
    .map(e => ({id: e.id || '', label: e.getAttribute('aria-label') || e.dataset.slide || ''})),
  title: document.title,
  standard: { kit: typeof window.DemoEngine !== 'undefined', dac_mode: document.documentElement.dataset.mode || '' },
  dom_words: (document.body.textContent || '').split(/\\s+/).filter(Boolean).length,
  visible_words: (document.body.innerText || '').split(/\\s+/).filter(Boolean).length })"""


def scan(text, terms):
    return {"forbidden": [t for t in terms if re.search(r"(?<![A-Za-z0-9])" + re.escape(t) + r"(?![A-Za-z0-9])", text, re.I)],
            "twelve_digit_numbers": sorted(set(re.findall(r"(?<!\d)\d{12}(?!\d)", text))),
            "dollars": sorted(set(re.findall(r"(?:\$|USD\s?)\s?\d[\d,.]*", text))),
            "dates": sorted(set(re.findall(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}\b|\b20\d\d-\d\d-\d\d\b|\bQ[1-4]\s?20\d\d\b", text)))}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("demo"); ap.add_argument("outdir")
    ap.add_argument("--query", default=""); ap.add_argument("--viewport", default="1688x1130")
    ap.add_argument("--theme", default="dark", choices=["dark", "light"]); ap.add_argument("--key", default="ArrowRight")
    ap.add_argument("--max", type=int, default=60); ap.add_argument("--settle", type=float, default=1.2)
    ap.add_argument("--forbid", default="")
    a = ap.parse_args()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("needs the Python playwright package with Chromium (pip install playwright; playwright install chromium)")
    url = a.demo if re.match(r"^[a-z]+://", a.demo) else "file://" + os.path.abspath(a.demo)
    url += a.query
    w, h = (int(x) for x in a.viewport.lower().split("x"))
    terms = [t.strip() for t in a.forbid.split(",") if t.strip()]
    os.makedirs(a.outdir, exist_ok=True)
    screens, seen, idle = [], set(), 0
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": w, "height": h}, color_scheme=a.theme)
        pg.goto(url); pg.wait_for_timeout(a.settle * 2000)
        marks = pg.evaluate(JS_LANDMARKS)
        for n in range(a.max + 1):
            if n:
                pg.keyboard.press(a.key); pg.wait_for_timeout(a.settle * 1000)
            st = pg.evaluate(JS_STATE)
            key = hashlib.sha256((st.pop("shown") + "|" + st["where"] + "|" + " ".join(st["controls"])).encode()).hexdigest()
            if key in seen:
                idle += 1
                if idle >= 5:
                    break
                continue
            idle = 0; seen.add(key)
            shot = os.path.join(a.outdir, f"screen-{len(screens) + 1:02d}.png")
            pg.screenshot(path=shot)
            screens.append({"n": len(screens) + 1, "after_presses": n, "screenshot": shot, **st, "scan": scan(st["text"], terms)})
        b.close()
    hidden = marks["dom_words"] - marks["visible_words"]
    inv = {"demo": a.demo, "url": url, "viewport": a.viewport, "theme": a.theme, "key": a.key, **marks,
           "hidden_words_estimate": hidden, "screens": screens}
    json.dump(inv, open(os.path.join(a.outdir, "inventory.json"), "w"), indent=1, ensure_ascii=False)
    md = [f"# Demo inventory: {marks['title'] or a.demo}", "",
          f"Opened `{url}` at {a.viewport}, {a.theme}; walked with {a.key}. {len(screens)} distinct screens.",
          ("Screen modes: this demo is built on the demo-engine template (mode: " + (marks["standard"]["dac_mode"] or "unknown") + "), so use its words for the staff panel, modes and keys."
           if marks["standard"]["kit"] else "Screen modes: this demo is not built on the demo-engine template. Describe what it actually does for entry, modes and keys, and add 'not the shared mode names' where it differs."), "",
          f"Declared sections: {len(marks['sections'])}. Words in the file but not on screen: about {hidden} "
          "(hidden notes or panels; anyone with developer tools can read them, so no spoken-only line may live there).", ""]
    if marks["sections"]:
        md += ["## Declared sections", ""] + [f"{i}. {s['label']} (`{s['id']}`)" for i, s in enumerate(marks["sections"], 1)] + [""]
    for s in screens:
        md += [f"## Screen {s['n']} (after {s['after_presses']} presses) · `{os.path.basename(s['screenshot'])}`", "",
               "**Headings:** " + (" · ".join(s["headings"]) or "none"), "",
               "**Controls (exact labels):** " + (" · ".join(f"'{c}'" for c in s["controls"][:40]) or "none"), ""]
        flags = {k: v for k, v in s["scan"].items() if v}
        if flags:
            md += [f"**Check before quoting:** {json.dumps(flags, ensure_ascii=False)}", ""]
        md += ["<details><summary>Visible text</summary>", "", s["text"][:3000], "", "</details>", ""]
    md += ["## Not covered", "", "Clicks, tabs, menus and timed playback were not exercised. Drive every click path the talk track uses and time every screen that plays by itself."]
    open(os.path.join(a.outdir, "inventory.md"), "w").write("\n".join(md) + "\n")
    print(f"{len(screens)} screens -> {os.path.join(a.outdir, 'inventory.md')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
