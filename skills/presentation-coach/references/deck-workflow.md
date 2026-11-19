# Deck workflow: one spec, one source deck, checked builds

The pattern: the talk-track spec is the single source of the spoken content; the deck is one hand-edited HTML file;
everything else is generated and checked. Nothing that leaves the room is edited by hand after the checks.

```
figures.md ──┐
             ├─> talk-track-spec.json ──> build_talk_track.py ──> talk-track.html   (rehearse from this)
brief ───────┘            │
                          └─> notes_from_spec.py ──> deck.html ──> build.py ──> dist/NAME.html        (present from this, N = notes)
                                                                             └─> dist/NAME-share.html  (send this; notes removed)
checks: untraced_numbers.py (every number sourced) · sensitivity_check.py (no forbidden term) · runtime_check.js (mechanics)
```

## 1. Start the deck

Copy `assets/deck-template.html` next to your talk (for example `deck.html`). It is a complete six-slide sample about a
fictional product. Replace the content slide by slide, using the story arc you chose from `templates/`; keep the
`<script>` and the chrome as they are.

What the template already does:

| Mechanic | How |
|---|---|
| 16:9 stage | A 1920x1080 stage scaled to the window; design in real pixels |
| Click-through builds | `data-len="K"` on a slide; `class="b" data-b="0..K-1"` on its parts. Arrow keys, space, PgDn step every build, then the slide |
| Build styles | `b` (rise), `b pop` (snap in), `b from-l` / `from-r` (slide in), `stag` on a list (children cascade), `draw` on an SVG path with `pathLength="1"` (the line is drawn in) |
| Count-ups | `<span data-count="42">42</span>`, `data-dec="1"` for one decimal; runs when its build appears |
| Interactive tracks | Slide 3 shows a hook: the marker, fill and detail panel follow the build, and nodes are clickable. Add hooks in `HOOK` (slide index -> function) |
| Slide transitions | Fade and slide between slides; builds ease in |
| Speaker notes | `N` opens the notes panel (presenter build only) |
| Help | `?` lists every key; `Esc` closes panels |
| Theme | Dark by default; `L` or the corner button toggles; the choice is saved; `?theme=light` or `?theme=dark` overrides |
| Still mode | `?still` shows every slide at its final build with no motion or chrome (for PDF and review stills) |
| Reduced motion | `prefers-reduced-motion` keeps the builds and drops the movement |
| Navigation | `1`-`9` jump, `Home` / `End`, `#3` in the URL opens slide 3, swipe on touch screens |
| Print | Every slide on its own 1920x1080 page |

Design rules the model decks followed: one claim-led headline per slide (a sentence, not a topic); one visual idea per
slide; slide text short enough that the talk track adds something; every surface colour paired with its text colour
in both themes (edit the CSS variables, not individual elements); a system font stack so the file needs no fonts.

Branding: replace the `#mark` symbol with your own SVG and the `--brand` colour. For images, fonts or SVG files, use
build placeholders, resolved relative to the deck file: `{{img:brand/cover.jpg}}`, `{{font:brand/MyFont.woff2}}`,
`{{svg:brand/logo.svg}}`, `{{raw:snippet.html}}`. The build inlines them, so the output stays one file.

## 2. Write the notes from the spec

```bash
python3 scripts/notes_from_spec.py talk-track-spec.json deck.html
```

The spec needs one segment per slide. The script rewrites the block between `/* NOTES:BEGIN */` and
`/* NOTES:END */` and prints words and estimates per slide, matching the rehearsal page. Never hand-edit the notes;
edit the spec and rerun.

## 3. Build presenter and share copies

```bash
python3 scripts/build.py deck.html --out-dir dist --name my-talk
```

`dist/my-talk.html` keeps the notes. `dist/my-talk-share.html` has the notes block and panel removed from the file
(not hidden), and the build refuses to write it if any trace of the notes remains.

## 4. Check before anything leaves the room

```bash
python3 scripts/untraced_numbers.py --spec talk-track-spec.json --deck dist/my-talk-share.html \
    --figures figures.md [--figures brief.md] [--allow allow.txt]
python3 scripts/sensitivity_check.py --config sensitivity.json dist/my-talk-share.html talk-track.html \
    [dist/my-talk.html --warn-only my-talk.html]
python3 scripts/offline_check.py dist/my-talk.html dist/my-talk-share.html talk-track.html
node scripts/runtime_check.js dist/my-talk.html dist/my-talk-share.html --shots review
```

- **One file, no requests.** `offline_check.py` reads each file (no browser) and lists every reference that would
  fetch something: script and image sources, stylesheets, `url()` in CSS, `fetch` and imports in scripts. The
  target is `requests=0 local=0`. A static scan cannot see a URL assembled at run time, so when you can, also open
  the file with the network off and watch for requests, and say which of the two you ran.
- **Every number has a source.** `untraced_numbers.py` lists each numeric claim (digits, spelled numbers, dates,
  multipliers, ordinals) in the spec and the deck, and whether a line in the figures file carries the same value
  with shared keywords. It always exits 0; the last line is `UNSOURCED: N`. For each unsourced row: add the real
  source line, reword, or cut. The allow list is for logistics only (slot length, clock checkpoints). It is a
  screening aid: it misses claims phrased differently from their source, and a match is co-occurrence, not proof.
- **No forbidden term ships.** `sensitivity_check.py` takes every term and pattern from your config
  (`examples/sensitivity.example.json`); nothing is hard-coded. A hit in the share build exits 1. The presenter build
  may legitimately carry internal context in its notes; scan it with `--warn-only`.
- **The mechanics work.** `runtime_check.js` walks every build of every slide, the theme toggle, `?still`, notes in
  presenter versus share, help and print, and with `--shots` writes stills in both themes. Look at the stills
  yourself before calling the deck done. Install once with `npm i -D playwright && npx playwright install chromium`,
  or point `PLAYWRIGHT_PATH` at an existing install.

PDF backup (optional): open `dist/my-talk-share.html?still` in Chromium and print to PDF with background graphics, or
script it with Playwright's `page.pdf({width: '1920px', height: '1080px', printBackground: true})`.

## 5. The figures file

One line per fact, with its source, in plain language (see `examples/acme-figures.md`):

```
- 42 database upgrades completed in the pilot. Source: pilot report, 2026-03-04, owner: the platform lead.
```

- A number goes on a slide or into the talk track only after it has a line here.
- Proposals and targets get lines too, labelled as such ("Proposed next phase: …", "Target: …"), so nobody hears a
  target as a result.
- The speaker confirms every line before the talk; the coach never edits a figure, only flags it.

## 6. Native PowerPoint (optional)

```bash
python3 scripts/pptx/build_pptx.py deck.html --spec talk-track-spec.json --out dist/ --name my-talk \
    [--sensitivity sensitivity.json] [--preview] [--states-override states.json] [--font-sans Arial --font-mono Consolas]
```

Writes `my-talk-dark.pptx`, `my-talk-light.pptx` (speaker notes from the spec) and `my-talk-share-dark.pptx`,
`my-talk-share-light.pptx` (no notes parts at all), every element a real PowerPoint shape or text box, then validates
them. Sample output: `examples/pptx/`.

**HTML or PPTX?** Present from the HTML when you can: it is the source, it has every motion exactly, and it runs in
any browser offline. Build the PPTX when the venue, the host or a co-presenter needs PowerPoint, when someone will
edit the slides after you, or when the file must go through a channel that only takes Office documents. Make every
content change in the HTML and rebuild; never hand-edit the PPTX and the HTML separately.

**Dependencies**, checked at start with an install hint for anything missing (exit 3):

| Needed for | What | Install |
|---|---|---|
| Extraction | Node 18+, Playwright, Playwright's Chromium | `npm i -D playwright && npx playwright install chromium` (or set `PLAYWRIGHT_PATH`) |
| Building | Python 3.9+, python-pptx, lxml, Pillow | `pip install python-pptx lxml pillow` |
| `--preview` | numpy; fontconfig's `fc-match` for fonts | `pip install numpy` |

**How it works.** The build states come from the deck's own markup: one state per build step (`data-len`) of every
`<section class="slide">`, written to `states.json` in the work folder; `--states-override` takes `{"3": 5}` (slide to
states) or a full list. `dom_extract.js` opens each state in Chromium in both themes, records every box, line, icon
and text run with its paint order and the build class that reveals it, and saves a reference still.
`pptx_native.py` turns the records into shapes and a click-by-click timing tree. `validate_pptx.py` checks the result;
`native_preview.py` renders each click state again from the PPTX and compares it with the HTML still.

**Animation map**

| HTML | PowerPoint |
|---|---|
| Each click-through build step | One click; its entrances and exits run together, in the HTML's order, with its stagger delays |
| Build 0 of a slide | Entrances that start with the slide (With Previous) |
| `.b` rise, `.stag` children | Float In (fade + rise), staggered |
| `.from-l`, `.from-r`, `.swap .now` | Fly In (fade + short travel) |
| `.pop` | Zoom (fade + scale from 86 %) |
| `.draw` strokes | Wipe in the direction the stroke is drawn |
| `.trk .mark` moving marker | Motion path, written relative to the shape's own position, one leg per click |
| `.trk .fill` filling bar | Wipe from left |
| State changes (current step, done, highlighted panel) | The new look fades in over the old; the old disappears underneath |
| `[data-count]` count-up | The final value appears, then a grow-and-shrink emphasis |
| `.comet`, `.wire .pt` ambient motion | Spin and looping motion paths, repeating until the slide ends |
| Gate ping | Grow + fade, twice |
| Slide transitions | Fade |

Any element can force a motion with `data-pptx="fade|float|fly-l|fly-r|fly-up|fly-down|zoom|wipe"`.

**Not 1:1 with the HTML**

- Count-ups do not count; the final number appears and pulses.
- Eased CSS curves become PowerPoint's linear or accelerate/decelerate timing; the slide transition drops the 40 px drift.
- Fonts: the HTML uses the system font stack; the PPTX names one typeface each for sans and mono (default Arial and
  Consolas, set with `--font-sans` / `--font-mono`). Line breaks are the browser's, so a wider font can run past its box
  rather than re-wrap; light weights render as regular.
- CSS blur glows and soft shadows are approximated with gradient ovals and native shadow and glow effects.
- Flow dots loop on a fixed path; the HTML fades them along the path with a different easing.
- Icons are SVG with a PNG fallback rendered at 6x; very old PowerPoint versions show only the PNG.
- Interactive clicks on track nodes (jumping to a step) do not exist in PowerPoint; the clicks walk the steps in order.

**Honest limits**

- No PowerPoint playback test: there is no PowerPoint here. The checks are structural (XML parses, every timing target
  exists, clicks per slide equal the HTML's build steps minus one, notes only in presenter files, neutral docProps) plus
  the preview, which is our own renderer of the file, not PowerPoint's. Click through each file in PowerPoint (and
  Keynote or Google Slides if that is where it will run) before you present from it.
- Motion paths assume PowerPoint applies them relative to the shape's layout position (`origin="layout"`,
  `pathEditMode="relative"`), and each leg starts where the previous leg ended.
- Wipe directions assume `wipe(left)` reveals from the left edge and `wipe(up)` from the top, as PowerPoint writes them;
  a stroke drawn right to left or bottom to top gets the opposite edge.
- The preview does not draw shape rotation, and it uses whatever local fonts `fc-match` returns.
- Only the template's build classes are mapped. Custom motion in your own CSS falls back to a fade unless you add a
  `data-pptx` hint.
