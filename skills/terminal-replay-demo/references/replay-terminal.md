# The replay terminal

The visitor should see what the product's own terminal shows, nothing more.

## 1. Look like the real terminal

- Draw the session the way the real CLI draws it: its prompt, its tool-call blocks, its status words, its tabs. Take
  the look from the recorded casts (render them to text or stills and compare), not from memory.
- **No invented product UI.** No dashboards, buttons, progress widgets or panels the product doesn't have. The
  surroundings (a step rail, a step card with a short lead, chips the visitor clicks) are the demo's chrome and must
  look like the demo's, not like the product's.
- The approver's pane is a second terminal tab with that person's identity, because in the product the approval
  happens at the approver's own terminal. Label the tab when it is recreated.
- Name the component for what it is, e.g. the accessible name "Recreated terminal session".
- One component draws every surface (Drive it, Watch it, the loop, the video), so a fix lands everywhere at once.
  The `terminal-replay` skill's player works this way.

## 2. Two ways to play, one state

| Mode | What the visitor does |
|---|---|
| **Watch it** | Play, pause, restart; chapters jump to a step; the caption follows. |
| **Drive it** | Click a chip or type. Typed input is keyword-matched to the step's chips; no match prints a short nudge and the chips again. Nothing calls a model. |

Switching modes keeps the scenario and the step. Deep links (`?scene=<id>`) let the presenter and the checks open any
state directly.

Drive-it design that held up:
- 2 to 4 chips per step: go on, ask a question (answered from the run's own artifacts), show the evidence files, and
  at the gate decide (approve or decline).
- "Show me the evidence files": report file names open a viewer of the real (redacted) report.
- "Inject an issue": at a few steps, a chip plays a seeded-fault or real-failure cut with its own label and product
  version, then returns to the clean run.
- An end card with "replay" and "back to start". Every path returns somewhere.

## 3. Scrollback

A visitor will scroll up to re-read. Make the terminal body scroll:
- It follows the newest line while the visitor is at the bottom.
- Scrolling up pauses following; a "Jump to latest ↓" button resumes it.
- A render that was never scrolled sits at the bottom, so the video frames don't change.
- Declare the scrollback as a scroll region for the clip check, so lines scrolled away aren't counted as cut.

## 4. Readable in both themes

Ship and check dark and light, and a colour-safe mode. Which theme opens by default is the venue's call; write it in
the staff quick-start, and offer `?theme=` and a key (L) to switch.

| Check | Bar |
|---|---|
| Text contrast | every text run at least 4.5:1 |
| Non-text contrast | accent strokes at least 3:1 |
| Meaning survives light | no hue role (green pass, red fail, amber warning) turns to neutral ink in light |
| Colour-safe | status words get a glyph (✓ ✕ !), so meaning never depends on hue |
| Smallest labels | 14 px at the presenter's window size |
| Monospace face | embedded in the file, so a borrowed laptop draws the same columns |

## 5. Booth inputs

The venue decides the input. Assume keyboard and mouse, no touchscreen and no speakers unless told otherwise:
- Every action works with a click and with a key; nothing needs a hover or a gesture only.
- No audio. Use short on-screen captions and visual cues instead of narration.
- Long text goes in a scroll region with a visible scrollbar, never in a fixed box that hides overflow.
