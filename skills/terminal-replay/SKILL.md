---
name: terminal-replay
description: Build a recreated terminal-session replay, with no slides, for any presentation or demo. From one session script (prompts, typed commands, output, pauses, captions and approve, decline or inject-an-issue branches) it writes one self-contained offline HTML replay with typing speed, ?speed=, play, pause, restart, step-through, a timing table, a "Recreated, not live" badge, light and dark themes and reduced motion. Optionally renders the same script to an MP4 loop with the official Remotion agent skills. Use when someone wants to show a CLI, an agent or a command-line workflow without running it live.
license: MIT
metadata:
  version: "1.0.0"
---

# Terminal replay

One session script in, one HTML file out. The replay shows a command-line session the way it ran (or the way it is
designed to run), typed and printed at a readable speed, with a badge on screen that says it is recreated. It needs
Python 3.9+ to build and a browser to view. Nothing else.

Files (paths relative to this folder):

| Path | What |
|---|---|
| `references/session-format.md` | The session script: scenes, events, choices, timing, inline colour markup |
| `assets/term-player.js`, `assets/term-player.css` | The player (vanilla JS) and its token theme; the demo-engine template embeds the same two files |
| `assets/replay-template.html` | The page the build fills in |
| `scripts/build_replay.py` | Validate, print the timing table, write the single HTML file, optional video timeline |
| `scripts/offline_check.py` | Static proof that the file makes 0 network requests |
| `examples/acme-ledger-session.json` | A worked example for a fictional product; `examples/out/` holds its build |

## Workflow

1. **Get the real session first.** Ask for a transcript, a terminal recording or the commands and their output.
   Every line in the script comes from that source. If a line is designed rather than recorded, the session's
   `label` says so ("A scripted recreation with fictional data"). Never invent output for a real product and
   present it as real.
2. **Write the script** (`references/session-format.md`). Split it into scenes at the moments the audience should
   notice: a plan, an approval, a result. Give each scene a `stage` label and a one-line `caption`.
3. **Add the branches the story needs:** an approval gate with `approve` and `decline` choices, and, when it helps,
   an `inject` choice that plays a failure and comes back to the gate. Set `auto` on a choice scene to pick the path
   autoplay takes.
4. **Keep it readable.** Long output becomes a few representative lines and a `[[dim:…]]` summary line. Keep the
   recorded order. Do not drop a step, an error or a result to make the story cleaner.
5. **Build and check:**
   ```bash
   python3 scripts/build_replay.py session.json replay.html [--speed 1] [--forbid "codename,client"]
   python3 scripts/offline_check.py replay.html          # must print requests=0 local=0 ... PASS
   ```
   The build refuses to write a file that contains a forbidden term (exit 2) and refuses an invalid script (exit 1).
6. **Look at it.** Open the file, play it once at `?speed=1` and once with `?step`, try every chip, switch the theme
   with L, and turn on reduced motion in the OS. If you cannot open a browser, say the replay is visually
   unverified and give the user these steps.
7. **Report** the timing table, the offline-check line, what you looked at, and any line you could not trace to the
   source session.

## Using it inside a deck or demo

- **Link it:** keep `replay.html` next to the deck only if the deck may load local files. For one self-contained
  deck, embed the player instead.
- **Embed it:** the demo-engine template (`templates/demo-engine/` in this repository) inlines `term-player.js`,
  `term-player.css` and a session script into one slide. Copy your script into its `content/` folder.
- **URL options:** `?speed=2`, `?theme=light`, `?step`, `?autoplay=0`, `?scene=<id>`. Keys: Space play or pause,
  L theme. With focus on the terminal, Space or Enter steps when step mode is on.

## Video, optional (Remotion)

For a wall screen or kiosk with no browser, render the same script to an MP4 loop. This path is opt-in: the HTML
replay above needs no Node and no Remotion.

> **Licence.** The Remotion library has its own licence. Its licence page
> ([remotion.dev/license](https://www.remotion.dev/license)) says: "Remotion is free to use for individuals and
> companies up to three people. Obtaining a Company License is required only for entities ineligible for the Free
> License." Check your own eligibility before you install it; the official `remotion-license` skill covers the terms.

1. **Install the official Remotion agent skills** from their publisher, listed on skills.sh at
   [skills.sh/remotion-dev/skills](https://www.skills.sh/remotion-dev/skills):
   ```bash
   npx skills add remotion-dev/skills
   ```
   The publisher's README ([github.com/remotion-dev/skills](https://github.com/remotion-dev/skills)) also lists
   `npx remotion skills add` inside an existing Remotion project. Review third-party skills before your agent
   follows them. Remotion's own documentation: [remotion.dev/docs](https://www.remotion.dev/docs).
2. **Export the timeline** from this skill. It holds the main path as timed events with frame numbers, so the video
   and the HTML replay agree:
   ```bash
   python3 scripts/build_replay.py session.json --check --timeline timeline.json --fps 30
   ```
3. **Have the agent follow the official skills:** `remotion-create` to scaffold a project and one composition that
   reads `timeline.json` (its `duration_frames`, `prompt`, `badge` and `events`), `remotion-captions` to show each
   scene's `caption`, and `remotion-render` to render the MP4. Ask for: the same token colours as
   `assets/term-player.css`, the badge visible on every frame, typed text drawn from each event's `frame` and
   `dur_frames`, and an embedded monospace font so the columns hold.
4. **Check the video** like the page: stills at the gate and at the result, compared with the HTML at the same scene;
   the badge present; the length matches the timing table.

## Rules

- The badge stays on screen in every mode and frame. A replay without it reads as a live run.
- One session per script. Do not splice two runs into one scene; make two scenes and label both.
- Fictional data says so in `label` and `footer`.
- No secrets, account numbers, internal hostnames or customer names in a script. Put the user's own forbidden terms
  in `forbidden_terms` or `--forbid`.
- The HTML must stay one file: `offline_check.py` passes with `requests=0 local=0`.
