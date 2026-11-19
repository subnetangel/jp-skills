#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build a booth talk track (walk-up demo) from one JSON booth spec.

Usage:
  build_booth_talk_track.py booth.json OUTDIR [--prefix NAME] [--suffix -vX.Y.Z] [--wpm 120] [--builder PATH] [--no-pdf]

Writes to OUTDIR:
  <prefix>-talk-track.html        staff page (talk-track-page format: Full / Script only / Learn). Spoken-only lines are
                                  replaced by a pointer, and their terms are forbidden, so the page is safe on any screen.
  <prefix>-talk-track-print.pdf   print layout (A4, light, notes open). Carries the spoken-only lines. Staff print only.
  <prefix>-card-text.md           two-sided card text: front = one path's beats, back = hooks, map, short answers.
  <prefix>-card-preview.pdf       the card text laid out at the spec's minimum font sizes, to prove it fits.
  <prefix>-cheat-sheet.pdf        (when the spec has "cheat_sheet") one page for anyone covering the station.
  <prefix>-timing.md              the timing table (also printed).
  <prefix>-checks.json            every check and its result.

Timing model (estimate, not measured delivery): a beat lasts
  words(say) / wpm + clicks_s + wait_s + max(screen_s, words(over) / wpm)
where `over` lines are said while the screen plays. Words are counted with talk-track-page's own counter. Each path
must leave at least `min_spare` (default 0.10) of its budget unused, or the build fails (exit 3).

Exit codes: 0 ok, 2 hygiene refusal (forbidden or spoken-only term where it must not be), 3 timing short of spare,
4 the card or the cheat sheet does not fit at the required sizes.
Needs Python 3.9+. PDFs need the Python Playwright package with Chromium; without it they are skipped and reported.
"""
import argparse
import html
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
# The talk-track builder ships with the presentation-coach skill. Installed side by side, it sits next to this skill.
BUILDER_PATHS = [os.path.join(HERE, "..", "..", "presentation-coach", "scripts", "build_talk_track.py")]


def load_builder(path):
    cands = [path] if path else [os.environ.get("TALK_TRACK_BUILDER", "")] + BUILDER_PATHS
    for c in cands:
        p = os.path.expanduser(c) if c else ""
        if p and os.path.isfile(p):
            spec = importlib.util.spec_from_file_location("build_talk_track", p)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return p, mod
    sys.exit("talk-track builder not found; install the presentation-coach skill next to this one, set "
             "TALK_TRACK_BUILDER, or pass --builder PATH/build_talk_track.py")


def words(mod, lines):
    return sum(mod.spoken_words(f'"{t}"') for t in lines)


def beat_time(mod, b, wpm):
    say, over = words(mod, b.get("say", [])), words(mod, b.get("over", []))
    t = say / wpm * 60 + b.get("clicks_s", 0) + b.get("wait_s", 0) + max(b.get("screen_s", 0), over / wpm * 60)
    return say + over, t


def timing(spec, mod, wpm):
    out = []
    for p in spec["paths"]:
        rows, cum = [], 0.0
        for bid in p["beats"]:
            b = spec["beats"][bid]
            w, t = beat_time(mod, b, wpm)
            cum += t
            rows.append({"beat": bid, "title": b["title"], "words": w, "seconds": t, "cum": cum,
                         "screen_s": b.get("screen_s", 0), "screen_source": b.get("screen_source", "")})
        spare = (p["budget_s"] - cum) / p["budget_s"]
        out.append({"id": p["id"], "name": p["name"], "budget_s": p["budget_s"], "total_s": cum,
                    "words": sum(r["words"] for r in rows), "spare": spare, "rows": rows})
    return out


def q(lines):
    return " ".join(f'"{t}"' for t in lines)


def beat_paragraph(n, b):
    # one chip per comma-separated action: a chip never wraps, so one long chip runs off the card
    clicks = " ".join(f"[click: {c.strip()}]" for c in b.get("click", "").split(", ") if c.strip())
    head = f"**{n}. {b['title']}** {clicks}".strip()   # no middle-dot meta strings (sloplint 63)
    parts = [head]
    if b.get("say"):
        parts.append(q(b["say"]))
    if b.get("over"):
        parts.append("[act: while it plays] " + q(b["over"]))
    if b.get("cue"):
        parts.append(b["cue"])
    return " ".join(parts)


def tt_spec(spec, tim, mmss, wpm, staff):
    so = spec.get("spoken_only", {})
    segs = []
    for x in spec.get("sections", []):   # "lead": true sections (stance, qualifying questions) come before the paths
        if x.get("lead"):
            segs.append({"id": x["id"], "nav": x.get("nav", x["title"]), "title": x["title"], "purpose": x.get("intro", ""),
                         "script": [{"text": i, "anchor": False} for i in x["items"]]})
    for p, t in zip(spec["paths"], tim):
        script = []
        for n, bid in enumerate(p["beats"], 1):
            b = spec["beats"][bid]
            script.append({"text": beat_paragraph(n, b), "anchor": bool(b.get("anchor"))})
        notes = [f"{n} · {spec['beats'][bid]['title']}: lands \"{spec['beats'][bid].get('land', '')}\". "
                 f"{spec['beats'][bid].get('pace', '')} Source: {spec['beats'][bid].get('source', 'none given')}."
                 for n, bid in enumerate(p["beats"], 1)]
        segs.append({"id": f"p{p['id']}", "nav": p["name"], "title": p["name"],
                     "time": f"~{mmss(t['total_s'])} of {mmss(p['budget_s'])} · {round(t['spare'] * 100)}% spare (estimate)",
                     "purpose": p.get("purpose", ""), "warmth": p.get("warmth", ""), "competence": p.get("competence", ""),
                     "script": script, "transition": p.get("exit", ""), "count_transition": False,
                     "notes": notes + p.get("notes", []), "notes_title": "Why each beat, pace and sources"})
    extra = [x for x in spec.get("sections", []) if not x.get("lead")]
    held = spec.get("spoken_only_held")   # the owner held the line: it goes in no output, not even the print copy
    if so.get("lines") and held:
        extra.append({"id": "spoken-only", "title": "Spoken only: on hold",
                      "paragraphs": [spec.get("spoken_only_held_note", "A spoken-only line is on hold. Don't say it until the booth lead tells you.")]})
    elif so.get("lines"):
        if staff:
            extra.append({"id": "spoken-only", "title": "Spoken only: say it, never show it",
                          "intro": so.get("intro", "Say these aloud only when asked. Never on a screen, slide or shared file."),
                          "items": [f"{x.get('status', '')} · \"{x['text']}\"" if x.get("status") else f"\"{x['text']}\"" for x in so["lines"]]})
        else:
            extra.append({"id": "spoken-only", "title": "Spoken only",
                          "paragraphs": [so.get("pointer", "The spoken-only line is in the printed staff copy only, never on this page.")]})
    rows = []
    for t in tim:
        for r in t["rows"]:
            rows.append({"segment": f"{t['name']} · {r['title']}", "words": r["words"], "estimate": f"~{mmss(r['seconds'])}",
                         "checkpoint": f"cumulative ~{mmss(r['cum'])}" + (f" · screen {r['screen_s']:g} s" if r["screen_s"] else "")})
        rows.append({"segment": f"**{t['name']} total**", "words": t["words"], "estimate": f"~{mmss(t['total_s'])}",
                     "checkpoint": f"**budget {mmss(t['budget_s'])} · {round(t['spare'] * 100)}% spare**"})
    intro = (f"Each beat: spoken words at {wpm} wpm (planning assumption) + clicks + waits for the visitor + the screen's own "
             f"playing time; lines said over the screen overlap it. Estimates, not measured delivery: time one out-loud run.")
    return {
        "title": spec["title"], "subtitle": spec.get("subtitle", ""), "badge": spec.get("badge", "Staff only. Do not show visitors."),
        "doc_title": spec["title"] + " · booth talk track · STAFF ONLY",
        "heading": "Booth talk track: " + spec["title"],
        "cue_card": spec.get("cue_card"), "segments": segs, "close": spec.get("close"),
        "questions": spec.get("questions", []), "questions_intro": spec.get("questions_intro", "One or two sentences, then stop."),
        "extra_sections": extra,
        "timing": {"intro": intro, "rows": rows, "checkpoint_label": "Running total", "note": spec.get("timing_note", "")},
        "rehearsal": spec.get("rehearsal", []), "rehearsal_title": spec.get("rehearsal_title", "Rehearsal"),
        "footer": spec.get("footer", "Staff only."),
        # shortcut: the talk-track builder scans its own CSS too (font names, 'text-transform'), so terms are checked here
        # on visible text instead (visible_text); hand them back to the builder if it ever strips <style> before scanning.
        "forbidden_terms": [],
    }


STAFF_CSS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "staff-page.css")


def restyle(path):
    """Swap the talk-track page's stylesheet for this skill's staff stylesheet (same class names)."""
    page = open(path, encoding="utf-8").read()
    css = open(STAFF_CSS, encoding="utf-8").read()
    page, n = re.subn(r"<style>.*?</style>", lambda m: "<style>\n" + css + "</style>", page, count=1, flags=re.S)
    if n != 1:
        sys.exit("restyle: no <style> block in " + path)
    open(path, "w", encoding="utf-8").write(page)


def visible_text(page):
    page = re.sub(r"<(style|script)\b.*?</\1>", " ", page, flags=re.S | re.I)
    return html.unescape(re.sub(r"<[^>]+>", " ", page))


def card_md(spec):
    c, so = spec["card"], spec.get("spoken_only", {})
    p = next(x for x in spec["paths"] if x["id"] == c["front_path"])
    f = [f"# {c['title']}", "", f"## Front · {p['name']} · {c['front_min_pt']} pt or larger", ""]
    for n, bid in enumerate(p["beats"], 1):
        b = spec["beats"][bid]
        cb = b.get("card", {})
        f.append(f"{n}. **{b['title']}** · CLICK: {cb.get('click', b.get('click', ''))} · SAY: {cb.get('say', q(b.get('say', [])))}")
    f += ["", f"## Back · {c['back_min_pt']} pt or larger", ""]
    for blk in c["back"]:
        f.append(f"### {blk['title']}")
        f += [f"- {x}" for x in blk["items"]] + [""]
    if so.get("lines") and c.get("staff_line") and not spec.get("spoken_only_held"):
        f += ["### Say, don't show (staff card only, never on a screen or in HTML)"]
        f += [f"- {x.get('status', '')} · \"{x['text']}\"" for x in so["lines"]] + [""]
    return "\n".join(f)


def card_html(spec):
    c, so = spec["card"], spec.get("spoken_only", {})
    e = lambda s: html.escape(s, quote=False)
    md_b = lambda s: re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", e(s))
    p = next(x for x in spec["paths"] if x["id"] == c["front_path"])
    front = "".join(f"<li><b>{e(spec['beats'][b]['title'])}</b> <i>{e(spec['beats'][b].get('card', {}).get('click', ''))}</i><br>"
                    f"{e(spec['beats'][b].get('card', {}).get('say', ''))}</li>" for b in p["beats"])
    back = "".join(f"<h3>{e(k['title'])}</h3><ul>" + "".join(f"<li>{md_b(x)}</li>" for x in k["items"]) + "</ul>" for k in c["back"])
    if so.get("lines") and c.get("staff_line") and not spec.get("spoken_only_held"):
        back += "<h3>Say, don't show</h3><ul>" + "".join(f"<li>{e(x.get('status', ''))} · {e(x['text'])}</li>" for x in so["lines"]) + "</ul>"
    w, h = c.get("size_mm", [210, 148])
    css = (f"@page{{size:{w}mm {h}mm;margin:0}}body{{margin:0;font-family:Arial,Helvetica,sans-serif;color:#000}}"
           f".side{{width:{w}mm;height:{h}mm;box-sizing:border-box;padding:6mm;overflow:hidden;break-after:page}}"
           f".front{{font-size:{c['front_min_pt']}pt;line-height:1.18}}.back{{font-size:{c['back_min_pt']}pt;line-height:1.15;column-count:2;column-gap:5mm}}"
           "h2{font-size:1.15em;margin:0 0 2mm}h3{font-size:1em;margin:1.5mm 0 .5mm;break-after:avoid}ul,ol{margin:0;padding-left:5mm}"
           "li{margin:0 0 1.2mm}i{font-style:normal;color:#333}")
    lab = f"<p style='margin:2mm 0 0;font-size:.8em'>{e(spec.get('for_label', ''))}</p>" if spec.get("for_label") else ""
    return (f"<!doctype html><html lang=en><meta charset=utf-8><title>{e(c['title'])}</title><style>{css}</style><body>"
            f"<section class='side front'><h2>{e(c['title'])} · front</h2><ol>{front}</ol>{lab}</section>"
            f"<section class='side back'><h2>{e(c['title'])} · back</h2>{back}{lab}</section></body></html>")


def sheet_html(spec):
    """The one-page cheat sheet for anyone covering the station: blocks in columns, one page, at min_pt or larger."""
    c = spec["cheat_sheet"]
    e = lambda s: html.escape(s, quote=False)
    md_b = lambda s: re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", e(s))
    w, h = c.get("size_mm", [210, 297])
    blocks = "".join(f"<div class=blk><h3>{e(k['title'])}</h3>" + "".join(f"<p>{md_b(x)}</p>" for x in k.get("paragraphs", []))
                     + (f"<ul>{''.join(f'<li>{md_b(x)}</li>' for x in k['items'])}</ul>" if k.get("items") else "") + "</div>"
                     for k in c["blocks"])
    css = (f"@page{{size:{w}mm {h}mm;margin:0}}body{{margin:0;font-family:Arial,Helvetica,sans-serif;color:#000}}"
           f".side{{width:{w}mm;height:{h}mm;box-sizing:border-box;padding:8mm;overflow:hidden}}"
           f".side{{font-size:{c.get('min_pt', 9)}pt;line-height:1.2}}.cols{{column-count:{c.get('columns', 2)};column-gap:6mm}}"
           "h1{font-size:1.6em;margin:0}h2{font-size:1em;font-weight:400;margin:.5mm 0 3mm;color:#222}"
           ".bar{height:1.5mm;background:" + c.get("accent", "#FF4D8B") + ";margin:0 0 2mm}"
           ".blk{break-inside:avoid;margin:0 0 2.5mm}h3{font-size:1.05em;margin:0 0 .8mm;text-transform:uppercase;letter-spacing:.04em}"
           "p{margin:0 0 1mm}ul{margin:0;padding-left:4.5mm}li{margin:0 0 .6mm}.foot{font-size:.9em;color:#222;margin-top:2mm}")
    return (f"<!doctype html><html lang=en><meta charset=utf-8><title>{e(c['title'])}</title><style>{css}</style><body>"
            f"<section class=side><div class=bar></div><h1>{e(c['title'])}</h1><h2>{e(c.get('subtitle', ''))}</h2>"
            f"<div class=cols>{blocks}</div><p class=foot>{md_b(c.get('footer', ''))}</p></section></body></html>")


def pdf(html_path, pdf_path, card=False):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"made": False, "why": "python playwright not installed"}
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto("file://" + os.path.abspath(html_path))
        res = {"made": True}
        if card:
            res["overflow"] = pg.evaluate("() => [...document.querySelectorAll('.side')].map(s => s.scrollHeight > s.clientHeight + 1 || s.scrollWidth > s.clientWidth + 1)")
            pg.pdf(path=pdf_path, prefer_css_page_size=True, print_background=True)
        else:
            pg.emulate_media(media="print")
            pg.pdf(path=pdf_path, format="A4", margin={"top": "12mm", "bottom": "12mm", "left": "12mm", "right": "12mm"}, print_background=True)
        b.close()
    return res


def hits(text, terms):
    return [t for t in terms if re.search(r"(?<![A-Za-z0-9])" + re.escape(t) + r"(?![A-Za-z0-9])", text, re.I)]


def scan(text, spec):
    allowed = set(spec.get("allowed_long_ids", spec.get("allowed_account_ids", [])))
    return {"forbidden": hits(text, spec.get("forbidden_terms", [])),
            "long_ids": sorted({m for m in re.findall(r"(?<!\d)\d{12}(?!\d)", text) if m not in allowed}),
            "dollars": re.findall(r"(?:\$|USD\s?)\s?\d[\d,.]*", text),
            "dates": re.findall(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}\b|\b20\d\d-\d\d-\d\d\b|\bQ[1-4]\s?20\d\d\b", text)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec"); ap.add_argument("outdir")
    ap.add_argument("--prefix", default="booth"); ap.add_argument("--wpm", type=int, default=0)
    ap.add_argument("--suffix", default="", help="added before each extension, e.g. -v1.2.0 -> NAME-talk-track-v1.2.0.html")
    ap.add_argument("--builder", default=""); ap.add_argument("--no-pdf", action="store_true")
    a = ap.parse_args()
    spec = json.load(open(a.spec, encoding="utf-8"))
    wpm = a.wpm or spec.get("wpm", 120)
    bpath, mod = load_builder(a.builder)
    os.makedirs(a.outdir, exist_ok=True)
    out = lambda s: os.path.join(a.outdir, f"{a.prefix}-{os.path.splitext(s)[0]}{a.suffix}{os.path.splitext(s)[1]}")
    label = spec.get("for_label", "")   # e.g. "For <demo> v1.2.0": stamped on the outputs the spec doesn't word itself
    checks = {"for": label, "builder": bpath, "wpm": wpm} if label else {"builder": bpath, "wpm": wpm}

    tim = timing(spec, mod, wpm)
    min_spare = spec.get("min_spare", 0.10)
    lines = ["| Path | Beat | Words | Estimate | Running total | Screen plays |", "|---|---|---:|---:|---:|---|"]
    for t in tim:
        for r in t["rows"]:
            lines.append(f"| {t['name']} | {r['title']} | {r['words']} | {mod.mmss(r['seconds'])} | {mod.mmss(r['cum'])} | "
                         + (f"{r['screen_s']:g} s ({r['screen_source']})" if r["screen_s"] else "") + " |")
        lines.append(f"| **{t['name']}** | **total** | **{t['words']}** | **{mod.mmss(t['total_s'])}** | budget {mod.mmss(t['budget_s'])} | "
                     f"**{t['spare'] * 100:.1f}% spare** |")
    table = "\n".join(lines)
    open(out("timing.md"), "w").write((f"{label}\n\n" if label else "") + f"Timing at {wpm} wpm (planning assumption; estimates, not measured delivery)\n\n{table}\n")
    print(table)
    checks["timing"] = [{"path": t["name"], "total_s": round(t["total_s"], 1), "budget_s": t["budget_s"], "spare": round(t["spare"], 3),
                         "ok": t["spare"] >= min_spare} for t in tim]
    short = [c for c in checks["timing"] if not c["ok"]]

    so_terms = spec.get("spoken_only", {}).get("terms", [])
    rc = 0
    with tempfile.TemporaryDirectory() as td:
        for staff in (False, True):
            js = os.path.join(td, f"tt-{staff}.json")
            json.dump(tt_spec(spec, tim, mod.mmss, wpm, staff), open(js, "w"), ensure_ascii=False)
            dest = os.path.join(td, "print.html") if staff else out("talk-track.html")
            r = subprocess.run([sys.executable, bpath, js, dest, "--wpm", str(wpm), "--quiet"], capture_output=True, text=True)
            if r.returncode:
                print(r.stderr.strip(), file=sys.stderr); return 2
            restyle(dest)
            if staff:   # print layout: open every collapsed note so paper shows it
                page = open(dest, encoding="utf-8").read().replace("<details>", "<details open>")
                open(dest, "w", encoding="utf-8").write(page)
                checks["print_pdf"] = {"made": False, "why": "--no-pdf"} if a.no_pdf else pdf(dest, out("talk-track-print.pdf"))
            if staff:
                pt = visible_text(open(dest, encoding="utf-8").read())
                checks["print_html"] = scan(pt, spec) | ({"spoken_only_terms": hits(pt, so_terms)} if spec.get("spoken_only_held") else {})
        screen_text = visible_text(open(out("talk-track.html"), encoding="utf-8").read())
        checks["screen_html"] = scan(screen_text, spec) | {"spoken_only_terms": hits(screen_text, so_terms)}
        md = card_md(spec) + (f"\n_{label}_\n" if label else "")
        open(out("card-text.md"), "w").write(md)
        checks["card_text"] = scan(md, spec) | ({} if spec["card"].get("staff_line") and not spec.get("spoken_only_held") else {"spoken_only_terms": hits(md, so_terms)})
        ch = os.path.join(td, "card.html")
        open(ch, "w", encoding="utf-8").write(card_html(spec))
        checks["card_pdf"] = {"made": False, "why": "--no-pdf"} if a.no_pdf else pdf(ch, out("card-preview.pdf"), card=True)
        if spec.get("cheat_sheet"):   # for anyone covering the station; spoken-only lines never go on it
            sh = os.path.join(td, "sheet.html")
            open(sh, "w", encoding="utf-8").write(sheet_html(spec))
            st = visible_text(open(sh, encoding="utf-8").read())
            checks["cheat_sheet"] = scan(st, spec) | {"spoken_only_terms": hits(st, so_terms)}
            checks["cheat_sheet_pdf"] = {"made": False, "why": "--no-pdf"} if a.no_pdf else pdf(sh, out("cheat-sheet.pdf"), card=True)

    bad = [k for k in ("screen_html", "print_html", "card_text", "cheat_sheet") if any(checks.get(k, {}).values())]
    if bad:
        rc = 2
        print("REFUSED: hygiene check failed in " + ", ".join(bad), file=sys.stderr)
    elif short:
        rc = 3
        print("FAILED: under the spare: " + ", ".join(c["path"] for c in short), file=sys.stderr)
    elif any(checks["card_pdf"].get("overflow", [])) or any(checks.get("cheat_sheet_pdf", {}).get("overflow", [])):
        rc = 4
        print("FAILED: the card or the cheat sheet overflows at the required sizes", file=sys.stderr)
    if rc:   # never leave a failing deliverable behind for someone to pick up; timing.md and checks.json stay
        for s in ("talk-track.html", "talk-track-print.pdf", "card-text.md", "card-preview.pdf", "cheat-sheet.pdf"):
            if os.path.exists(out(s)):
                os.remove(out(s))
    checks["exit"] = rc
    json.dump(checks, open(out("checks.json"), "w"), indent=1)
    print(json.dumps(checks, indent=1))
    return rc


if __name__ == "__main__":
    sys.exit(main())
