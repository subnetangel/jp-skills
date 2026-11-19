---
name: booth-talk-track
description: Write the spoken talk track, staff page, print copy, two-sided pocket card, one-page cheat sheet and 10-minute drill for a walk-up demo (booth, expo stand, demo lounge, kiosk with a person beside it), starting from an existing demo file or URL. Turns a presentation talk track or booth playbook into short click-this, say-this paths a staffer can say to a stranger who may leave at any moment, timed from spoken words plus screen time with at least 10% spare. Use when someone staffs or trains others to staff a demo station.
license: MIT
metadata:
  version: "1.0.0"
---

# Booth talk track

A booth visitor arrives unannounced and leaves when they like, so a booth talk track is a set of short **paths**
built from **beats**, not one timed talk. Each beat is "click this, say this" with a cue, timed from spoken words
plus what the screen plays by itself. Write for the person **covering the station cold**: rotating staff who never
built the demo. Outputs: a staff page (rehearsal-page format, with Learn mode), a print copy, a two-sided card, a
one-page cheat sheet, and a 10-minute drill.

**Install with:** `presentation-coach` (its talk-track builder, the "Demo booth playbook" mode, the coaching modules
and the evidence rules). The build looks for `../presentation-coach/scripts/build_talk_track.py` next to this skill;
set `TALK_TRACK_BUILDER` or pass `--builder` if it lives elsewhere. If the demo is built on the `demo-engine`
template, use its names for the staff panel and modes (its README, "Modes").

## Workflow

1. **Read the demo.** With a browser available: `python3 scripts/read_demo.py DEMO OUTDIR [--query "?idle=0"]
   [--forbid "a,b"]` walks the file or URL with → and writes every screen's headings, exact control labels and
   visible text, plus a hygiene scan. It needs the Python Playwright package with Chromium. Without it, read the
   HTML source yourself and list the screens, labels and on-screen claims by hand. Either way, drive each click
   path you will write and time every screen that plays by itself; a click you have not seen work is marked
   "verify in the drill".
2. **Use one vocabulary.** In every "how to drive it" line, name the staff panel, the screen modes (staffed, kiosk,
   presenter, wall loop), the loop and the keys the same way on every station. Where the demo differs, describe
   what it actually does. Put the station setup (open the panel, pick the mode, keys, idle, reset) in a `lead`
   section.
3. **Collect the approved lines:** hooks, the close, the one approved availability line, the Q&A, from the demo's
   own notes or playbook. Every claim gets a `source` (file and line, or URL). Never invent a number, customer, date
   or story.
4. **Write the spec** (`references/booth-spec.md`; example `examples/acme-booth.json`), outside any shared folder.
   Include lead sections (covering cold, station setup, stance, the two or three questions that pick the path),
   beats, paths (usually 30 s, 2 min, 5 min), situations (interruption, expert, skeptic, group, breakage),
   never-say, Q&A, close and reset, the drill, the card, the cheat sheet.
5. **Check the messaging guidance.** Put the organisation's current guidance in never-say. Default, unless the owner
   says otherwise: show only what is available today, combinations of available pieces, and items launching at the
   event; no preview-to-release stories; no product names that may not ship as shown. List every approved line the
   guidance puts in doubt (planned channels, future releases, "coming soon") for the owner. Flag, don't rewrite:
   approved wording is the owner's.
6. **Build:** `python3 scripts/build_booth_talk_track.py spec.json OUTDIR --prefix NAME`. Exit 3: a path has under
   10% spare; cut words or start the screen later, never "speak faster". Exit 2: hygiene refusal. Exit 4: the card or
   cheat sheet overflows. PDFs need Python Playwright; without it they are skipped and the build says so.
7. **Look at it:** the page in Full and Learn, the print PDF, the card preview, the cheat sheet. Say what you checked
   and what you could not open.
8. **Report:** the timing table, open items (unverified clicks, ⚠ answers, pending lines), lines the guidance puts in
   doubt, and deviations from the source playbook.

## Quick reference

| Rule | Why |
|---|---|
| Beat = words(say)/wpm + clicks + waits + max(screen plays, words said over it) | Staff talk over playback |
| Each path at least 10% spare at 120 wpm unless the speaker's rate is measured | Visitors interrupt |
| Spoken-only lines live in `spoken_only`: print copy only, refused on the page, card and cheat sheet | Staff open HTML on visitor screens; hidden demo notes are readable too |
| A short path runs long? Start the screen later and say what already happened | Cut preamble, not proof |
| Label recreated or seeded parts as such | Expert visitors ask |

## Decisions the brief may not make for you

- **The spec stays private:** it holds the spoken-only lines. Share only the built outputs.
- **`spoken_only` status:** `PENDING <owner>` until approved, then `APPROVED`. Pending lines say "check with the
  booth lead first".
- **`card.staff_line`:** false unless the owner asks for the line on a printed staff-only card.
- **⚠ (`confirm`):** an answer whose fact or wording still needs the owner, not an approved line.
- **Codenames** can't be named on the page (the build refuses them); the booth lead briefs them in person.

## Common mistakes

- Word counts "by eye" at a fast pace: the 2-minute path really runs 2:30. Use the build's count.
- Leaving the spoken-only line out, so staff can't find it. Put it in `spoken_only`.
- Clicks as prose inside the script: staff can't scan them. Use `click`; it renders as chips.
- No reset, no breakage plan, no drill: the second visitor sees the first visitor's screen.
- Guessing what a click does. Drive it, or mark "verify in the drill".
- Each demo's own names for its panel and modes: staff rotating between stations hear five vocabularies. Use one
  set of names and mark where a demo differs.

## Known limit

The talk-track builder scans its own stylesheet for forbidden terms too, so this build checks visible text itself
and passes no terms to it.
