#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build a self-contained HTML terminal replay (and optionally a video timeline) from one session script.

Usage:
  build_replay.py SESSION.json OUT.html [--speed 1] [--forbid "a,b"] [--timeline OUT.json --fps 30]
  build_replay.py SESSION.json --check            validate and print the timing table only

SESSION is JSON (YAML too when PyYAML happens to be installed). Format: references/session-format.md.

What it does
  * Validates the script: unique scene ids, every goto/next/auto points at a scene, known event types, at least one
    scene, a badge that says the run is recreated.
  * Prints the timing table for the main path (the path autoplay takes) at --speed, with the same formula the player
    uses: typed characters / type_cps + enter_ms, line_ms per output line or note, pauses as written, hold_ms before
    an automatic choice.
  * Inlines assets/term-player.css, assets/term-player.js and the script into assets/replay-template.html and writes
    ONE file. Nothing is fetched at run time; check it with scripts/offline_check.py.
  * Refuses to write (exit 2) when a forbidden term (session "forbidden_terms" plus --forbid) appears in the output.
  * --timeline writes the main path as timed events with frame numbers, for a video composition (see SKILL.md,
    "Video, optional").
Exit codes: 0 ok, 1 invalid script, 2 forbidden term. Python 3.9+, standard library only.
"""
import argparse
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent.parent
TAG = re.compile(r"\[\[(?:ok|warn|err|dim|em|cmd):([^\]]*)\]\]")
EVENTS = {"type", "out", "note", "pause", "caption", "stage", "clear"}
KINDS = {"approve", "decline", "inject", "next", "restart"}


def plain(s):
    return TAG.sub(r"\1", str(s))


def load(path):
    text = pathlib.Path(path).read_text(encoding="utf-8")
    if path.endswith((".yaml", ".yml")):
        try:
            import yaml  # optional; not required
        except ImportError:
            sys.exit("YAML needs PyYAML; convert the script to JSON or pip install pyyaml")
        return yaml.safe_load(text)
    return json.loads(text)


def tune(s):
    t = s.get("timing") or {}
    return {"type_cps": t.get("type_cps", 40), "enter_ms": t.get("enter_ms", 250),
            "line_ms": t.get("line_ms", 70), "hold_ms": t.get("hold_ms", 1800)}


def event_ms(ev, t):
    """Milliseconds one event takes at speed 1.

    >>> event_ms({"type": "type", "text": "ab"}, {"type_cps": 2, "enter_ms": 0, "line_ms": 0})
    1000.0
    """
    k = ev.get("type")
    if k == "type":
        return len(plain(ev["text"])) / t["type_cps"] * 1000 + t["enter_ms"]
    if k == "out":
        return len(ev.get("lines", [])) * ev.get("line_ms", t["line_ms"])
    if k == "note":
        return t["line_ms"]
    if k == "pause":
        return ev.get("ms", 0)
    return 0


def auto_next(sc):
    if sc.get("auto"):
        return sc["auto"]
    if sc.get("choices"):
        return sc["choices"][0]["goto"]
    return sc.get("next")


def validate(s):
    errs, ids = [], [sc.get("id") for sc in s.get("scenes", [])]
    if not ids:
        errs.append("no scenes")
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        errs.append(f"duplicate scene ids: {sorted(dup)}")
    known = set(ids)
    if s.get("start") and s["start"] not in known:
        errs.append(f"start '{s['start']}' is not a scene")
    if not re.search(r"recreat|replay|scripted|simulat", s.get("badge", "Recreated, not live"), re.I):
        errs.append("badge must say the session is recreated (default 'Recreated, not live')")
    for sc in s.get("scenes", []):
        for key in ("next", "auto"):
            if sc.get(key) and sc[key] not in known:
                errs.append(f"{sc['id']}: {key} '{sc[key]}' is not a scene")
        for c in sc.get("choices", []):
            if c.get("goto") not in known:
                errs.append(f"{sc['id']}: choice '{c.get('label')}' goes to unknown '{c.get('goto')}'")
            if c.get("kind", "next") not in KINDS:
                errs.append(f"{sc['id']}: choice kind '{c.get('kind')}' not in {sorted(KINDS)}")
        for ev in sc.get("events", []):
            if ev.get("type") not in EVENTS:
                errs.append(f"{sc['id']}: unknown event type '{ev.get('type')}'")
    return errs


def main_path(s, speed):
    t, by = tune(s), {sc["id"]: sc for sc in s["scenes"]}
    rows, seen, cur = [], set(), s.get("start") or s["scenes"][0]["id"]
    while cur and cur in by and cur not in seen:
        seen.add(cur)
        sc = by[cur]
        ms = sum(event_ms(e, t) for e in sc.get("events", [])) + (t["hold_ms"] if sc.get("choices") else 0)
        rows.append((cur, sc.get("stage", ""), ms / speed, sc))
        cur = auto_next(sc)
    return rows


def timeline(s, speed, fps):
    t, out, clock = tune(s), [], 0.0
    for sid, stage, _, sc in main_path(s, speed):
        out.append({"frame": round(clock / 1000 * fps), "ms": round(clock), "type": "scene", "id": sid,
                    "stage": stage, "caption": plain(sc.get("caption", ""))})
        for ev in sc.get("events", []):
            d = event_ms(ev, t) / speed
            item = {"frame": round(clock / 1000 * fps), "ms": round(clock), "dur_frames": max(1, round(d / 1000 * fps)),
                    **{k: v for k, v in ev.items() if k != "line_ms"}}
            if "text" in item:
                item["text"] = plain(item["text"])
            if "lines" in item:
                item["lines"] = [plain(x) for x in item["lines"]]
            out.append(item)
            clock += d
        if sc.get("choices"):
            out.append({"frame": round(clock / 1000 * fps), "ms": round(clock), "type": "choice",
                        "chosen": auto_next(sc), "labels": [c["label"] for c in sc["choices"]]})
            clock += t["hold_ms"] / speed
    return {"fps": fps, "speed": speed, "duration_frames": round(clock / 1000 * fps) + fps,
            "badge": s.get("badge", "Recreated, not live"), "prompt": s.get("prompt", "$ "), "events": out}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("session")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--forbid", default="")
    ap.add_argument("--timeline")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    s = load(a.session)
    errs = validate(s)
    if errs:
        print("INVALID:\n  " + "\n  ".join(errs), file=sys.stderr)
        return 1
    total = 0.0
    print(f"{'scene':<16} {'stage':<14} {'seconds':>8}")
    for sid, stage, ms, _ in main_path(s, a.speed):
        total += ms
        print(f"{sid:<16} {stage:<14} {ms / 1000:>8.1f}")
    print(f"TIMING: main path ~{total / 1000:.1f} s at speed {a.speed:g}")
    if a.timeline:
        pathlib.Path(a.timeline).write_text(json.dumps(timeline(s, a.speed, a.fps), indent=1), encoding="utf-8")
        print(f"timeline -> {a.timeline}")
    if a.check or not a.out:
        return 0
    tpl = (HERE / "assets" / "replay-template.html").read_text(encoding="utf-8")
    data = json.dumps({k: v for k, v in s.items() if k != "forbidden_terms"}, ensure_ascii=False).replace("</", "<\\/")
    page = (tpl.replace("{{css}}", (HERE / "assets" / "term-player.css").read_text(encoding="utf-8"))
               .replace("{{js}}", (HERE / "assets" / "term-player.js").read_text(encoding="utf-8"))
               .replace("{{session}}", data)
               .replace("{{title}}", _esc(s.get("title", "Terminal replay")))
               .replace("{{label}}", _esc(s.get("label", "A scripted recreation of a session. Nothing here runs live.")))
               .replace("{{footer}}", _esc(s.get("footer", ""))))
    terms = [x.strip() for x in s.get("forbidden_terms", []) + a.forbid.split(",") if x.strip()]
    hits = [x for x in terms if re.search(r"(?<![A-Za-z0-9])" + re.escape(x) + r"(?![A-Za-z0-9])", page, re.I)]
    if hits:
        print("REFUSED: forbidden terms present: " + ", ".join(hits), file=sys.stderr)
        return 2
    pathlib.Path(a.out).write_text(page, encoding="utf-8")
    print(f"wrote {a.out} ({len(page.encode('utf-8')):,} bytes)")
    return 0


def _esc(x):
    return str(x).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


if __name__ == "__main__":
    sys.exit(main())
