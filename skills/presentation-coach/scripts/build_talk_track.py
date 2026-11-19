#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Render a presenter-only talk-track page (self-contained HTML) from a JSON spec.

Usage:
  build_talk_track.py spec.json out.html [--wpm 120] [--forbid "term,term"] [--md out.md] [--quiet]

What it does
  * Emits the page: sticky header with PRESENTER ONLY badge, section nav and view modes (Full / Script only / Learn),
    how-to-use card with the cue legend, cue card, one card per segment (purpose, warmth and competence notes, script
    with cue chips and anchor lines, transition, collapsible guardrails), close, likely questions, timing, rehearsal.
  * Counts spoken words per segment (text inside straight double quotes when a paragraph has them, else the whole
    paragraph; cue chips and marks excluded) and prints a timing estimate at --wpm plus the segment's pause seconds.
    With "timing": {"auto": true} the timing table is filled from those counts.
  * Scans the finished page for forbidden terms (spec "forbidden_terms" plus --forbid) and refuses to write if any
    appear, so codenames and internal names never reach a page that leaves the machine.

Inline markup inside any script text, transition, proposal or cue-card line
  [pause]  [pause: stop, look up]      amber chip, a real stop
  [slow]   [slow: for the comparison]              blue chip, drop the pace
  [soft]   [soft: an invitation, not a sell]             violet chip, lower volume, warmer tone ("softer")
  [click: the number]  [point: at the chart]  [move: toward the room]  [act: let the loop run]   green chip
  [room]   [room: optional, skip if behind]           pink chip, a question or a show of hands for the room
  **key phrase**                                    underlined anchor words (what Learn mode keeps visible)

--md out.md also writes the same talk track as plain markdown (cue card, segments, questions, rehearsal).

Python 3.9+, standard library only.
"""
import argparse
import html
import json
import re
import sys

CSS = """  :root{
    --bg:#0f141b; --panel:#171e28; --line:#2a3442; --text:#e8edf3; --muted:#9aa7b8;
    --pause:#ffb547; --slow:#6fc3ff; --soft:#c99cff; --act:#7ee08a; --warm:#ff8fb8; --comp:#6fc3ff; --prop:#ffd866;
  }
  *{box-sizing:border-box}
  html{scroll-behavior:smooth}
  body{margin:0;background:var(--bg);color:var(--text);font:18px/1.6 system-ui,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
  header{position:sticky;top:0;z-index:5;background:rgba(15,20,27,.96);border-bottom:1px solid var(--line);backdrop-filter:blur(6px)}
  .bar{max-width:980px;margin:0 auto;padding:10px 20px;display:flex;gap:14px;align-items:center;flex-wrap:wrap}
  .badge{background:#c4103f;color:#fff;font-size:12px;font-weight:700;letter-spacing:.08em;padding:3px 8px;border-radius:4px}
  nav a{color:var(--muted);text-decoration:none;font-size:15px;margin-right:10px}
  nav a:hover{color:var(--text)}
  .modes{margin-left:auto;display:flex;gap:6px}
  .modes button{background:var(--panel);color:var(--text);border:1px solid var(--line);border-radius:6px;padding:5px 10px;font-size:14px;cursor:pointer}
  .modes button.on{border-color:var(--slow);color:var(--slow)}
  main{max-width:980px;margin:0 auto;padding:24px 20px 80px}
  h1{font-size:30px;line-height:1.25;margin:10px 0 4px}
  h2{font-size:24px;margin:0}
  h3{font-size:15px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin:22px 0 8px}
  .sub{color:var(--muted);font-size:15px}
  .card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:22px 24px;margin:22px 0}
  .cuecard{border-color:var(--slow)}
  .cuecard .msg{font-size:22px;line-height:1.4;margin:6px 0 14px}
  .cuecard ol{margin:0 0 12px 20px;padding:0}
  .ask{border-left:4px solid var(--warm);padding:8px 14px;background:#1e1a24;border-radius:4px}
  .slidehead{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap;border-bottom:1px solid var(--line);padding-bottom:10px}
  .time{font-family:ui-monospace,Menlo,monospace;font-size:14px;color:var(--muted)}
  .purpose{color:var(--muted);margin:10px 0 0}
  .lens{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:14px 0 4px}
  .lens div{font-size:15px;padding:10px 12px;border-radius:8px;background:#121821;border:1px solid var(--line)}
  .lens b{display:block;font-size:12px;letter-spacing:.08em;text-transform:uppercase;margin-bottom:2px}
  .w b{color:var(--warm)} .c b{color:var(--comp)}
  .script p{font-size:21px;line-height:1.7;margin:0 0 16px}
  .script p.anchor{border-left:3px solid var(--slow);padding-left:14px}
  .cue{font-size:14px;font-weight:600;border-radius:4px;padding:1px 7px;margin:0 2px;white-space:nowrap;font-family:ui-monospace,Menlo,monospace}
  .pause{color:var(--pause);background:rgba(255,181,71,.12)}
  .slow{color:var(--slow);background:rgba(111,195,255,.12)}
  .soft{color:var(--soft);background:rgba(201,156,255,.12)}
  .act{color:var(--act);background:rgba(126,224,138,.12)}
  .room{color:var(--warm);background:rgba(255,143,184,.14)}
  em.k{font-style:normal;border-bottom:2px solid var(--slow)}
  .prop{border:1px dashed var(--prop);border-radius:8px;padding:8px 12px;margin:0 0 16px}
  .prop small{color:var(--prop);font-size:12px;letter-spacing:.06em;text-transform:uppercase;display:block}
  .trans{background:#121821;border-radius:8px;padding:10px 14px;font-size:18px}
  .trans b{color:var(--act);font-size:12px;letter-spacing:.08em;text-transform:uppercase;display:block}
  details{margin-top:14px;border-top:1px solid var(--line);padding-top:10px}
  summary{cursor:pointer;color:var(--muted);font-size:15px}
  details ul{font-size:16px;margin:8px 0 0 0;padding-left:20px}
  .legend span{margin-right:8px}
  table{border-collapse:collapse;width:100%;font-size:15px}
  td,th{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left}
  th{color:var(--muted);font-weight:600}
  td.n{text-align:right;font-family:ui-monospace,Menlo,monospace}
  body.script-only .cue, body.script-only .lens, body.script-only details, body.script-only .purpose{display:none}
  body.learn .script p:not(.anchor){filter:blur(6px);cursor:pointer;transition:filter .15s}
  body.learn .script p.revealed{filter:none}
  body.learn .script p.anchor{filter:none}
  footer{color:var(--muted);font-size:13px;max-width:980px;margin:0 auto;padding:0 20px 40px}
  @media print{
    header{position:static} .modes{display:none}
    body{background:#fff;color:#000;font-size:12pt}
    .card{break-inside:avoid;background:#fff;border-color:#999}
    .script p{font-size:13pt}
    .lens div,.trans{background:#f4f4f4}
  }
"""

JS = """  const btns=document.querySelectorAll('.modes button');
  btns.forEach(b=>b.addEventListener('click',()=>{
    btns.forEach(x=>x.classList.remove('on')); b.classList.add('on');
    document.body.classList.remove('script-only','learn');
    if(b.dataset.mode!=='full') document.body.classList.add(b.dataset.mode);
    document.querySelectorAll('.script p.revealed').forEach(p=>p.classList.remove('revealed'));
  }));
  document.querySelectorAll('.script p').forEach(p=>p.addEventListener('click',()=>{
    if(document.body.classList.contains('learn')) p.classList.toggle('revealed');
  }));
"""

METHOD_NOTE = ("Two lenses on every segment: <b style=\"color:var(--warm)\">warmth</b>, where you show you're on their side, "
               "and <b style=\"color:var(--comp)\">competence</b>, where the evidence earns trust (after Vanessa Van Edwards' "
               "warmth-and-competence lens). The cues use deliberate variation in pace, volume, melody, tonality, and pause "
               "(after Vinh Giang's five vocal foundations). This page is a practical synthesis inspired by their public teaching, "
               "not their method. Use only the cues that feel like you.")

CUE_RE = re.compile(r"\[(room|pause|slow|soft|softer|act|click|point|move)(?::\s*([^\]]*))?\]", re.I)
KEY_RE = re.compile(r"\*\*(.+?)\*\*")
CUE_CLASS = {"room": "room", "pause": "pause", "slow": "slow", "soft": "soft", "softer": "soft", "act": "act",
             "click": "act", "point": "act", "move": "act"}


def esc(s):
    return html.escape(str(s), quote=False)


def inline(text):
    """HTML-escape, then turn [cue: detail] into chips and **phrase** into anchor marks."""
    out = esc(text)

    def chip(m):
        kind = m.group(1).lower()
        detail = (m.group(2) or "").strip()
        cls = CUE_CLASS[kind]
        if kind in ("click", "point", "move"):
            label = f"{kind}: {detail}" if detail else kind
        elif kind == "act":
            label = detail or "act"
        elif kind == "room":
            label = f"ask the room · {detail}" if detail else "ask the room"
        else:
            base = "softer" if kind in ("soft", "softer") else kind
            label = f"{base} · {detail}" if detail else base
        return f'<span class="cue {cls}">{label}</span>'

    out = CUE_RE.sub(chip, out)
    return KEY_RE.sub(r'<em class="k">\1</em>', out)


def spoken_words(text):
    """Words meant to be spoken: inside straight double quotes when present, with cues and marks removed."""
    t = CUE_RE.sub(" ", text).replace("**", "")
    quoted = re.findall(r'"([^"]*)"', t)
    body = " ".join(quoted) if quoted else t
    return len([w for w in re.findall(r"\S+", body) if re.search(r"[A-Za-z0-9]", w)])


def mmss(seconds):
    s = int(round(seconds))
    return f"{s // 60}:{s % 60:02d}"


def spare_check(total_s, timing):
    """(passes, spare fraction, required fraction): the estimate must leave timing.min_spare (default 10%) of budget_s.

    >>> spare_check(270, {"budget_s": 300})[0], spare_check(271, {"budget_s": 300})[0]
    (True, False)
    """
    budget = float(timing["budget_s"])
    need = float(timing.get("min_spare", 0.10))
    spare = (budget - total_s) / budget if budget > 0 else -1.0
    return spare >= need, spare, need


def li_items(items):
    return "".join(f"<li>{inline(i)}</li>" for i in items)


def render(spec, wpm):
    title = spec["title"]
    badge = spec.get("badge", "PRESENTER ONLY · DO NOT SHARE")
    segs = spec.get("segments", [])
    counts = []
    for s in segs:
        words = sum(spoken_words(p["text"]) for p in s.get("script", []) if "text" in p)
        if s.get("transition") and s.get("count_transition", True):
            words += spoken_words(s["transition"])
        counts.append(words)
    # with auto timing, segment headers without an explicit "time" get the computed estimate, so the page agrees with itself
    if (spec.get("timing") or {}).get("auto"):
        cum = 0.0
        for i, s in enumerate(segs):
            est = counts[i] / wpm * 60 + float(s.get("pauses_s", 0))
            cum += est
            if not s.get("time"):
                s["time"] = f"~{mmss(est)} · cumulative ~{mmss(cum)} (estimate)"

    # ---- nav ----
    nav = ['<a href="#card">Cue card</a>'] if spec.get("cue_card") else []
    for i, s in enumerate(segs, 1):
        nav.append(f'<a href="#{esc(s.get("id", f"s{i}"))}">{esc(s.get("nav", str(i)))}</a>')
    if spec.get("close"):
        nav.append('<a href="#close">Close</a>')
    if spec.get("questions"):
        nav.append('<a href="#qa">Q&amp;A</a>')
    if spec.get("rehearsal"):
        nav.append('<a href="#rehearse">Rehearse</a>')

    parts = [f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(spec.get("doc_title", "Talk track · " + title + " · PRESENTER ONLY"))}</title>
<style>
{CSS}</style>
</head>
<body>
<header>
  <div class="bar">
    <span class="badge">{esc(badge)}</span>
    <nav>{"".join(nav)}</nav>
    <div class="modes" role="group" aria-label="View mode">
      <button data-mode="full" class="on">Full</button>
      <button data-mode="script-only">Script only</button>
      <button data-mode="learn">Learn</button>
    </div>
  </div>
</header>

<main>
  <h1>{esc(spec.get("heading", "Talk track: " + title))}</h1>
  <div class="sub">{inline(spec.get("subtitle", ""))}</div>
"""]

    if spec.get("how_to_use", True):
        parts.append(f"""
  <div class="card">
    <h3 style="margin-top:0">How to use this page</h3>
    <p style="margin:0 0 8px"><b>Full</b> shows everything. <b>Script only</b> hides cues and notes for a clean read-through. <b>Learn</b> blurs everything except the anchor lines (blue bar); say the blurred part from memory, then click it to check.</p>
    <p class="legend" style="margin:0;font-size:15px">
      <span class="cue pause">pause</span> a real stop, 1–2 s
      <span class="cue slow">slow</span> drop the pace for the meaning
      <span class="cue soft">softer</span> lower volume, warmer tone
      <span class="cue act">click / point / move</span>
      <span class="cue room">ask the room</span> optional; raise your own hand first, wait 2 s, react to what you see
    </p>
    <p style="margin:10px 0 0;font-size:15px;color:var(--muted)">{spec.get("method_note", METHOD_NOTE)}</p>
  </div>
""")

    cc = spec.get("cue_card")
    if cc:
        anchors = []
        for a in cc.get("anchors", []):
            if isinstance(a, dict):
                anchors.append(f"<li><b>{inline(a.get('label', ''))}</b> {inline(a.get('text', ''))}</li>")
            else:
                anchors.append(f"<li>{inline(a)}</li>")
        parts.append(f"""
  <div class="card cuecard" id="card">
    <h3 style="margin-top:0">Cue card</h3>
    <div class="msg">{inline(cc.get("message", ""))}</div>
    <ol>{"".join(anchors)}</ol>
    {f'<div class="ask"><b>ASK:</b> {inline(cc["ask"])}</div>' if cc.get("ask") else ""}
    {f'<p class="time" style="margin:12px 0 0">{inline(cc["reminders"])}</p>' if cc.get("reminders") else ""}
  </div>
""")

    for i, s in enumerate(segs, 1):
        sid = esc(s.get("id", f"s{i}"))
        body = []
        for p in s.get("script", []):
            if "proposal" in p:
                body.append(f'<div class="prop"><small>{inline(p.get("label", "Proposed change, for you to accept or reject"))}</small>{inline(p["proposal"])}</div>')
            elif "text" in p:
                cls = ' class="anchor"' if p.get("anchor") else ""
                body.append(f"<p{cls}>{inline(p['text'])}</p>")
        lens = ""
        if s.get("warmth") or s.get("competence"):
            lens = ('<div class="lens">'
                    + (f'<div class="w"><b>Warmth</b>{inline(s["warmth"])}</div>' if s.get("warmth") else "")
                    + (f'<div class="c"><b>Competence</b>{inline(s["competence"])}</div>' if s.get("competence") else "")
                    + "</div>")
        notes = ""
        if s.get("notes"):
            notes = (f'<details><summary>{esc(s.get("notes_title", "Guardrails for this segment"))}</summary>'
                     f'<ul>{li_items(s["notes"])}</ul></details>')
        parts.append(f"""
  <section class="card" id="{sid}">
    <div class="slidehead"><h2>{inline(s.get("title", f"Segment {i}"))}</h2><span class="time">{inline(s.get("time", ""))}</span></div>
    {f'<p class="purpose">Purpose: {inline(s["purpose"])}</p>' if s.get("purpose") else ""}
    {lens}
    <div class="script">
      {"".join(body)}
    </div>
    {f'<div class="trans"><b>Transition</b>{inline(s["transition"])}</div>' if s.get("transition") else ""}
    {notes}
  </section>
""")

    cl = spec.get("close")
    if cl:
        lines = "".join(("<p class=\"anchor\">" if p.get("anchor") else "<p>") + inline(p["text"]) + "</p>" for p in cl.get("script", []))
        parts.append(f"""
  <section class="card" id="close">
    <div class="slidehead"><h2>{inline(cl.get("title", "The close"))}</h2><span class="time">{inline(cl.get("time", ""))}</span></div>
    <div class="script">{lines}</div>
  </section>
""")

    qs = spec.get("questions")
    if qs:
        rows = "".join(f"<tr><td>{inline(q['q'])}</td><td>{'⚠ ' if q.get('confirm') else ''}{inline(q['a'])}</td></tr>" for q in qs)
        parts.append(f"""
  <section class="card" id="qa">
    <h2>Likely questions</h2>
    <p class="sub">{inline(spec.get("questions_intro", "Answer in one or two sentences, then stop. ⚠ marks an answer that needs a fact confirmed first."))}</p>
    <table><tr><th>Question</th><th>Answer</th></tr>{rows}</table>
  </section>
""")

    for x in spec.get("extra_sections", []):
        xid = f' id="{esc(x["id"])}"' if x.get("id") else ""
        parts.append(f"""
  <section class="card"{xid}>
    <h3 style="margin-top:0">{inline(x.get("title", ""))}</h3>
    {f'<p class="sub">{inline(x["intro"])}</p>' if x.get("intro") else ""}
    {"".join(f"<p>{inline(p)}</p>" for p in x.get("paragraphs", []))}
    {f'<ul>{li_items(x["items"])}</ul>' if x.get("items") else ""}
  </section>
""")

    tm = spec.get("timing")
    timing_rows = []
    if tm:
        if tm.get("auto"):
            cum = 0.0
            for i, s in enumerate(segs):
                est = counts[i] / wpm * 60 + float(s.get("pauses_s", 0))
                cum += est
                timing_rows.append({"segment": s.get("nav", str(i + 1)), "words": counts[i], "estimate": f"~{mmss(est)}",
                                    "checkpoint": s.get("checkpoint", "—")})
            total_words = sum(counts)
            total_pause = sum(float(s.get("pauses_s", 0)) for s in segs)
            total = total_words / wpm * 60 + total_pause
            intro = (f"{total_words:,} spoken words at {wpm} wpm (planning assumption), plus ~{int(round(total_pause))} s of pauses, clicks and "
                     f"transitions, comes to <b>~{mmss(total)}</b>.")
            if tm.get("budget_s"):
                room = float(tm["budget_s"]) - total
                intro += f" That leaves ~{mmss(max(room, 0))} of the {mmss(tm['budget_s'])} budget for interaction." if room >= 0 \
                    else f" That is ~{mmss(-room)} over the {mmss(tm['budget_s'])} budget."
                ok, pct, need = spare_check(total, tm)
                intro += (f" Spare: {pct:.0%} (target at least {need:.0%}): <b>{'PASS' if ok else 'FAIL'}</b>."
                          + ("" if ok else " Cut words or segments before rehearsing; do not plan to talk faster."))
            intro += " These are estimates, not measured delivery; a timed out-loud run is the real check."
            if tm.get("intro"):
                intro += " " + inline(tm["intro"])
        else:
            timing_rows = tm.get("rows", [])
            intro = inline(tm.get("intro", ""))
        rows = "".join(f'<tr><td>{esc(r.get("segment", ""))}</td><td class="n">{esc(r.get("words", ""))}</td>'
                       f'<td class="n">{esc(r.get("estimate", ""))}</td><td>{inline(r.get("checkpoint", "—"))}</td></tr>' for r in timing_rows)
        parts.append(f"""
  <section class="card" id="timing">
    <h2>Timing (estimates)</h2>
    <p class="sub">{intro}</p>
    <table><tr><th>Segment</th><th>Words</th><th>Estimate</th><th>{esc(tm.get("checkpoint_label", "Clock checkpoint"))}</th></tr>{rows}</table>
    {f'<p class="sub" style="margin-top:10px">{inline(tm["note"])}</p>' if tm.get("note") else ""}
  </section>
""")

    if spec.get("rehearsal"):
        parts.append(f"""
  <section class="card" id="rehearse">
    <h2>{esc(spec.get("rehearsal_title", "Rehearsal"))}</h2>
    <ol style="font-size:17px">{li_items(spec["rehearsal"])}</ol>
  </section>
""")

    parts.append(f"""</main>

<footer>{inline(spec.get("footer", "Presenter-only: contains notes and guardrails never shown to the audience."))}</footer>

<script>
{JS}</script>
</body>
</html>
""")
    return "".join(parts), counts


def to_markdown(spec, counts, wpm):
    """Plain-markdown copy of the talk track (same spec, same word counts), for print, review or a chat window."""
    def md(t):
        return CUE_RE.sub(lambda m: f"_[{m.group(1).lower()}{': ' + m.group(2).strip() if m.group(2) else ''}]_", str(t))
    title = spec.get("title", "Talk track")
    out = [f"# {spec.get('heading', 'Talk track: ' + title)}", ""]
    if spec.get("subtitle"):
        out += [md(spec["subtitle"]), ""]
    cc = spec.get("cue_card") or {}
    if cc:
        out += ["## Cue card", "", f"**Message:** {md(cc.get('message', ''))}", ""]
        for a in cc.get("anchors", []):
            out.append(f"- {md(a['label'] + ' ' + a['text']) if isinstance(a, dict) else md(a)}")
        out += ["", f"**Ask:** {md(cc.get('ask', ''))}", ""]
        if cc.get("reminders"):
            out += [f"_Reminders:_ {md(cc['reminders'])}", ""]
    total = 0.0
    for i, s in enumerate(spec.get("segments", [])):
        est = counts[i] / wpm * 60 + float(s.get("pauses_s", 0))
        total += est
        out += [f"## {s.get('title', f'Segment {i + 1}')}", "",
                f"_~{mmss(est)} (estimate), cumulative ~{mmss(total)}"
                + (f" · checkpoint: {s['checkpoint']}" if s.get("checkpoint") else "") + "_", ""]
        for k in ("purpose", "warmth", "competence"):
            if s.get(k):
                out.append(f"- **{k.capitalize()}:** {md(s[k])}")
        out.append("")
        for p in s.get("script", []):
            if "proposal" in p:
                out += [f"> **{p.get('label', 'Proposal')}:** {md(p['proposal'])}", ""]
            else:
                out += [("**Anchor:** " if p.get("anchor") else "") + md(p.get("text", "")), ""]
        if s.get("transition"):
            out += [f"_Transition:_ {md(s['transition'])}", ""]
        for n in s.get("notes", []):
            out.append(f"- Note: {md(n)}")
        if s.get("notes"):
            out.append("")
    if spec.get("questions"):
        out += ["## Likely questions", ""]
        for q in spec["questions"]:
            out += [f"**{'⚠ ' if q.get('confirm') else ''}{md(q['q'])}**", "", md(q["a"]), ""]
    if spec.get("rehearsal"):
        out += [f"## {spec.get('rehearsal_title', 'Rehearsal')}", ""]
        out += [f"{n}. {md(r)}" for n, r in enumerate(spec["rehearsal"], 1)] + [""]
    out += [f"_Total ~{mmss(total)} at {wpm} wpm, an estimate from spoken-word counts. Time a full run out loud._", ""]
    if spec.get("footer"):
        out += [md(spec["footer"]), ""]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("out")
    ap.add_argument("--wpm", type=int, default=120, help="planning speaking rate (default 120)")
    ap.add_argument("--forbid", default="", help="comma-separated terms that must not appear (adds to spec forbidden_terms)")
    ap.add_argument("--md", help="also write a plain-markdown copy of the talk track to this path")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    spec = json.load(open(a.spec, encoding="utf-8"))
    page, counts = render(spec, a.wpm)

    text = html.unescape(re.sub(r"<[^>]+>", " ", page))
    forbidden = [t.strip() for t in spec.get("forbidden_terms", []) + a.forbid.split(",") if t.strip()]
    hits = [t for t in forbidden if re.search(r"(?<![A-Za-z0-9])" + re.escape(t) + r"(?![A-Za-z0-9])", text, re.I)]
    if hits:
        print("REFUSED: forbidden terms present: " + ", ".join(hits), file=sys.stderr)
        return 2

    open(a.out, "w", encoding="utf-8").write(page)
    if a.md:
        open(a.md, "w", encoding="utf-8").write(to_markdown(spec, counts, a.wpm))
    if not a.quiet:
        segs = spec.get("segments", [])
        total = 0.0
        for i, s in enumerate(segs):
            est = counts[i] / a.wpm * 60 + float(s.get("pauses_s", 0))
            total += est
            print(f"segment {i + 1:>2}  {counts[i]:>5} words  ~{mmss(est)}  cumulative ~{mmss(total)}   {s.get('title', '')[:60]}")
        print(f"total {sum(counts):,} spoken words at {a.wpm} wpm -> ~{mmss(total)} (estimate, incl. pauses)  ->  {a.out}")
    tm = spec.get("timing") or {}
    if tm.get("auto") and tm.get("budget_s"):
        total = sum(counts[i] / a.wpm * 60 + float(s.get("pauses_s", 0)) for i, s in enumerate(spec.get("segments", [])))
        ok, pct, need = spare_check(total, tm)
        print(f"TIMING: ~{mmss(total)} of {mmss(tm['budget_s'])}, {pct:.0%} spare (target >= {need:.0%}): {'PASS' if ok else 'FAIL'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
