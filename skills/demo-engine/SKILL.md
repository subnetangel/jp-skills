---
name: demo-engine
description: Fill in the demo-engine template to make a single-file offline HTML demo for a booth, kiosk, wall screen or talk. The template has a scaling 16:9 slide engine with a slide picker, light and dark token themes, staffed, presenter, kiosk and wall-loop modes from URL options or one CONFIG block, a staff panel behind a hashed staff code, a recreated terminal ("Drive it") with approve, decline and inject-an-issue branches, a report viewer with human and JSON views, double-click launchers, and a stdlib build and offline check. Use when someone needs a walk-up or presenter demo that must run with no network.
license: MIT
metadata:
  version: "1.0.0"
---

# Demo engine

The template lives in `templates/demo-engine/` in this repository (copy it into this skill folder as `template/`
when you install the skill; INSTALL.md shows how). Its README is the reference: what each part does, the modes, the
URL options, how to re-skin with tokens and the 10-step "make it yours" list. This file is the procedure.

## Procedure

1. **Get the venue facts** before you edit anything: network (assume none), input (keyboard and mouse, touch, a
   clicker), screen size, audio (assume none), staffed or unattended, and which modes the event needs. Write them
   at the top of your notes as facts or as stated assumptions.
2. **Copy the template** next to the talk or event folder. Never edit the template in place.
3. **Figures first.** Replace `content/FIGURES.md` with the user's facts and sources. A number that has no line
   there does not go on a slide, in the session or in the report. Ask for the source; never invent one.
4. **Slides.** Edit `src/demo.src.html`. One `<section class="slide" data-title="…">` per slide; 6 to 10 slides
   suit a walk-up demo. Open on the visitor's problem, show the product working, show the evidence, say what it
   does not do, close with one next step. Mark anything recreated or illustrative on the slide itself.
5. **Drive it.** Write `content/session.json` with the terminal-replay skill's format, from a real transcript where
   one exists. Keep the badge. Add `approve`, `decline` and, if it helps, `inject` choices.
6. **Report.** Put a short, real-shaped report in `content/report.json` so the evidence is one click away.
7. **CONFIG.** Set `mode`, `idleSeconds`, `playlists` and `dwellSeconds`. Remember the wall loop always starts at
   the first item of its playlist.
8. **Skin.** Change only the token blocks in `src/engine.css`. Check contrast in both themes.
9. **Build and check:**
   ```bash
   python3 build.py src/demo.src.html dist/NAME.html --staff-code-file PATH --launchers
   python3 offline_check.py dist/NAME.html                      # requests=0 local=0 PASS
   ```
   Run the user's sensitivity check on the built file (the presentation-coach skill's `sensitivity_check.py`), and
   the number-source check on the slide text (`untraced_numbers.py`). Optionally run `tools/dom_smoke.js` with
   jsdom installed outside the repo.
10. **Look at it, or say you did not.** Open the file in each mode and both themes at the presenter's real window
    size, try every chip, the report, the picker and the staff panel, and turn on reduced motion. If you cannot
    open a browser, report the demo as visually unverified and list these steps for the user.
11. **Report:** the file's size and SHA-256, the offline-check line, the other check results, what you looked at,
    and what you did not test (the launchers on real macOS and Windows, real projectors).

## Rules

- **The staff code is a convenience gate, not security.** Only its SHA-256 goes in the file. Never write the code
  into a command line, a commit, a card, a log or a report. Nothing goes behind the panel that a visitor may not see.
- **Lines meant only to be spoken go in no HTML.** Put them in a staff-only print sheet (the booth-talk-track skill).
- **One file.** Fonts, images and video are inlined by the build. A font needs a licence that allows embedding,
  shipped next to it.
- **Honest labels.** The terminal says "Recreated, not live". Slides with sample or illustrative data say so.
- **No dependencies.** Keep the engine vanilla JS and CSS. If you want more motion, use CSS, and respect
  `prefers-reduced-motion`. Anything that moves for more than a few seconds needs a pause control.

## Related skills

`terminal-replay` (the session format and a standalone replay), `booth-talk-track` (what staff say at each slide),
`demo-cheat-sheet` (a one-page card for someone covering the station), `demo-best-practices` (the review checklist),
`presentation-coach` (talk track, figures file and checks).
