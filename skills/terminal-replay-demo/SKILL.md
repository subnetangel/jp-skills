---
name: terminal-replay-demo
description: Plan and build an honest offline booth, conference, kiosk or sales demo of a CLI or agent product from real recorded terminal sessions - capture in a test environment, keep only clean runs, redact, cut, replay in a recreated terminal inside one HTML file, with looping videos, real failure cases, a presenter mode, a release guard and the checks that catch what goes wrong at venues. Use when a demo must show real terminal sessions with no network, or when someone proposes screen-recording a run and editing out the hiccups.
license: MIT
metadata:
  version: "1.1.0"
---

# Terminal replay demo

Record real sessions of your CLI or agent in a test environment as terminal bytes, keep only clean runs, redact
them, and replay them in a recreated terminal inside one offline HTML file, with the same frames rendered to video
for the loops. **Every line on screen is the run's own, and every recreated part says so.**

The worked example throughout is one team's conference booth demo of an agent CLI. The notes say what that team did
and found, so you can see each rule applied. You need none of its files.

**Breaking the letter of these rules breaks their spirit.** A spliced run is a run that never happened, even if each
half was real.

For the replay itself (a session script, one HTML file, ?speed=, branches) use the `terminal-replay` skill. This
skill covers what comes before it: capturing real runs so the replay is true.

## When to use

- A demo must show a CLI or agent doing real work, where the venue has no usable network or no live environment.
- Staff will run it from their own laptops by double-clicking a file; screens are public.
- You need: a visitor-driven mode, a hands-free loop, real failure cases on demand, a fallback video.

Not for: a live demo against a real environment (do that instead if the network allows), product UI walkthroughs
(use a click-through tool), a narrated marketing video.

## The pipeline

```
capture (test environment) -> raw/<run>/ *.io *.timing + artifacts     private, never in git
  -> redact_cast.py -> redacted/<run>/                                  length-preserving
  -> cut_segment.py -> demo-cut/golden/<scenario>/  + RUN.md            label, renames, pause trims; results untouched
  -> scan_cut.py    -> SCAN.json = pass
  -> replay data (a session script per scenario, from the cut, sources cited)   terminal-replay skill
  -> one offline HTML (demo-engine template or terminal-replay)  -> release guard -> package + VERSION.txt -> checks
```

## Quick reference

| Step | Do | Never | Details |
|---|---|---|---|
| Capture | Test environment, read-only identity for agent turns, clean agent home, a one-line user prompt, workspace files for the rest, a run tag on everything | Rehearse the product on the fixture; type the human's approval from a script | `references/capture.md` |
| Golden bar | No host or tool-window cut, no re-plan or operator correction, gates pass first time, every step done, verdict PASS with file:line, **one product version per scenario** | Splice turns from two runs or two versions; keep a run the host cut | `references/capture.md` §3 |
| Faults | One seeded issue per disposable fixture, test environment only; record seeding, catch point, verbatim words, outcome | Seed anything outside the test environment; finish a cut the run didn't finish | `references/capture.md` §4 |
| Redact | Copy only; length-preserving in `.io`; second pass on the escape-free view; hex digests untouched | Edit raw; let the redactor copy screenshots | `scripts/redact_cast.py` |
| Scan | Fail on long numeric identifiers you did not allow, secret-like tokens, your deny list | Ship a build with a fail | `scripts/scan_cut.py` |
| Teardown | Delete only what this run's state names or tags; tag sweep; inventory diff = identical | Delete by name prefix | `references/capture.md` §6 |
| Cut | Banner label, same-length renames, pauses capped at 2 s, every edit logged in RUN.md | Edit a result, an error or a refusal | `scripts/cut_segment.py`, `references/replay-format.md` |
| Replay data | Events from the cut, in order, `…` where trimmed, sources in the generator's docstring | Write a line the run didn't print | `references/replay-format.md` §3-4 |
| Labels | Per segment, per fault, per approver pane, per version | "Shown as recorded" on a cut with a recreated pane | `references/replay-format.md` §6 |
| Terminal | The real CLI's look; Drive it and Watch it; scrollback; both themes and colour-safe, all checked | Invent product UI | `references/replay-terminal.md` |
| Video | Render the replay's own frames; H.264 from an ffmpeg that has `libx264` | Render before you've checked the renderer's licence | `references/video.md` |
| File | Everything inlined, fonts embedded, 0 requests, opens from file:// | Reference an installed font or a CDN | `references/packaging.md` §1 |
| Build | One build per demo, autopilot or presenter, staff controls behind a gesture; a share build only for copies posted outside the demo area | Spoken-only lines in any HTML | `references/packaging.md` §2 |
| Release | `RELEASED.txt`; every writer refuses a released name; build only from a committed tree | Rebuild under a released name | `scripts/release_guard.py` |
| Package | HTML, quick-start PDF, booth card PDF, loops, fallback video, VERSION.txt with hashes | Hand staff a file without a hash | `scripts/version_manifest.py` |
| Checks | Offline, sensitivity, entry, clip at the presenter's real window in both themes, motion order, 30-min soak, PDF fonts | Check only at 1920x1080 with your own fonts installed | `references/checks.md` |

## 1. Capture real sessions

Record bytes, not pixels: `scripts/record_pty.py` runs your CLI on a pty, types one prompt like a person, waits for
idle, quits, and writes `script`-format `.io` and `.timing` files that `scriptreplay` plays.

```bash
python3 scripts/record_pty.py --out raw/run-1/ --name turn1 --prompt-file prompts/run-1-turn1.md \
  --idle-regex '<your CLI idle marker>' --quiet 120 --quit-keys '/quit\r' -- <your-cli> chat
```

Before turn 1: inventory the environment, export the exact product version (commit and version into the run
folder), give the agent a fresh home with only your product installed, and put the facts the agent needs into
workspace files. The visible prompt stays one sentence a user would type. A fictional example:

> The ledger close for October is due. Match the North entity's bank lines, stop for our controller after the plan,
> and follow our posting rules.

Give the real fixtures the demo's synthetic names from the start, so the cut needs no renaming.

**A human approval** is typed by the approver at their own terminal, never by the driver. To record it for real, the
approver runs `script -T approval.timing -B approval.io` in their own terminal and approves there; that pair is its
own segment. If the capture used a product-supplied test approver instead, the cut shows a recreated pane, labelled.

**A new product version mid-schedule** doesn't touch finished scenarios: each scenario stays on the version it was
recorded on and shows that version on screen. A scenario moves to a new version only by re-recording all of it. The
worked example shipped scenarios on four versions side by side, each labelled.

**Discard, don't repair.** Anything short of the golden bar goes to `raw/discarded-<run>/` with a reason, and you
rerun on a fixed fixture. The worked example kept every failure with its raw evidence in an index; several became
honest "real failure" cuts. Full protocol: `references/capture.md`.

## 2. Golden cuts and replay data

The cut is still a recording. Its only edits are the label banner, same-length synthetic names, pauses capped at
2 s and, if the human's approval was scripted in the capture, a recreated approver pane over the run's real
handoff, labelled as recreated.

```bash
python3 scripts/redact_cast.py private/redact-rules.json raw/run-1 redacted/run-1
python3 scripts/cut_segment.py --src redacted/run-1/turn1 --dst demo-cut/golden/close/01-turn1 \
  --label "Recreated from a real run in a test environment · synthetic names" --names private/names.json \
  --max-gap 2 --changes demo-cut/golden/close/RUN.md
python3 scripts/scan_cut.py demo-cut/ --deny private/deny.json --json demo-cut/golden/close/SCAN.json
```

The private config files stay out of git and out of the package: `redact-rules.json` (your real identifiers,
regex rules, split-token rules), `names.json` (`[["old", "new"], …]`, same lengths), `deny.json`
(`{"deny": {"rule": "regex"}}`). Each script's docstring shows the format.

Then write the replay data: one session script per scenario (the `terminal-replay` format), with 2 to 4 choices at
a step that needs them. One generator script per scenario reads the cut and cites file and replay time for what it
keeps and what it drops. Timing is compressed for reading (the worked example: typing 60 chars/s, prose 260 chars/s,
45 ms per output line); real times and real durations stay on screen as captions. Rules: `references/replay-format.md`.

## 3. The replay terminal

- It looks like the product's real terminal, taken from the casts. **No invented product UI.** The demo's own
  chrome (step rail, step card, chips) is visibly the demo's.
- **Drive it:** chips and typed input, keyword-matched to the step's chips; no model call; a nudge on no match.
- **Watch it:** play, pause, scrub, chapter jumps.
- **Scrollback** follows the newest line until the visitor scrolls up; "Jump to latest" resumes.
- **Inject an issue:** a few steps offer real fault cuts with their own label and version, then return to the clean
  run.
- **Both themes** plus a colour-safe mode; text 4.5:1 and strokes 3:1 in each; the monospace face embedded.

Details: `references/replay-terminal.md`.

## 4. Loops and the fallback video

Render the replay's own frames to video, one per scenario and theme, so a fix to the terminal reaches the video on
the next render. The `terminal-replay` skill's "Video, optional" section uses the official Remotion agent skills;
check the Remotion licence for your organisation first. Without Remotion, record the page in a headless browser and
encode H.264 with any ffmpeg that lists `libx264`. Details: `references/video.md`.

## 5. One offline HTML file

- Inline everything: JS, CSS, images, SVG, fonts as base64 woff2. 0 network requests. Opens by double-click from
  `file://`. Prefer one file over two linked files.
- **One build per demo.** Every station runs the same file, on autopilot or with a presenter. Staff controls sit
  behind a staff gesture and a staff code checked against a hash (the demo-engine template does this); the demo is
  visitor-safe on load. Lines meant to be spoken only never enter any HTML; they go in staff-only print sheets.
- **Share build (optional)**, only for a copy posted outside the demo area: the same source with the staff controls,
  speaker notes and code hash removed from the file, and a build that fails if any survive.
- **Release guard.** `RELEASED.txt` lists each released file's SHA-256 and name. Every writer refuses a path with a
  released version; a fix is a new version; release builds refuse an uncommitted tree.
- **Package:** the booth HTML, a one-page staff quick-start, the booth card (2-, 5- and 10-minute paths), the loops,
  the fallback video and `VERSION.txt` (version, build time, commit, SHA-256 and bytes of every file, runs with
  their product versions).
- **Talk track and cheat sheet:** use the `booth-talk-track` and `demo-cheat-sheet` skills.

```bash
python3 scripts/release_guard.py dirty . app/src build && \
python3 scripts/release_guard.py check dist/Demo-v1.5.html dist/package/Demo-v1.5 && \
python3 scripts/version_manifest.py dist/package/Demo-v1.5 --version v1.5 --demo Demo-v1.5.html --notes notes.txt
# after the upload:
python3 scripts/release_guard.py record dist/Demo-v1.5.html
```

Details: `references/packaging.md`.

## 6. Screen modes

A booth demo needs at least a staffed-laptop mode, a wall-screen mode (a locked, hands-free playlist) and a
presenter mode. Use the shared names, keys and link options in `demo-best-practices` (`screen-modes.md`); the
`demo-engine` template implements them.

## 7. Checks

Run them on the exact file you upload, with a fontconfig that hides your installed brand fonts
(`templates/fonts-embedded-only.conf`).

| Check | Command or method | Pass |
|---|---|---|
| Offline, static | `python3 scripts/offline_check.py Demo.html` | requests=0 local=0 |
| Offline, in a browser | `node scripts/offline_check.mjs Demo.html --keys "ArrowRight*40"` (Playwright) | 0 requests, 0 errors, 0 fonts failed |
| Sensitivity | `python3 scripts/scan_cut.py dist/ data/ demo-cut/ --deny private/deny.json` | verdict pass, labels present |
| Entry | first builds animate in when entered forward; final at once under reduced motion | opacity starts below 0.6, ends at 1 |
| Clip | `node scripts/clip_check.mjs Demo.html --states states.txt --scrollers ".tbody" --viewports <presenter's real window>,1920x1080,1280x800 --modes "dark=,light=&theme=light"` | 0 cut text runs, 0 cut control boxes, both themes |
| Motion | sample every frame of the sequences that tell the story; assert order and spacing | in order, spaced as designed |
| Soak | every locked playlist 30 min, offline: heap, DOM nodes, timer drift, items seen | heap and nodes within +25%, drift p99 < 250 ms |
| PDF fonts | `python3 scripts/pdf_fonts_check.py --allow <faces> package/*.pdf` | only your faces, no Type3 |
| Release guard | `python3 scripts/release_guard.py --self-test` | all cases pass |

The `.mjs` checks need Node 20+ with Playwright and Chromium. Without them, run the static offline check, say the
browser checks were not run, and give the user the commands. Name the browsers staff may use in the quick-start
and open the file once by double-click in each. Ask the presenter for a screenshot of their browser window and use
that size for the clip check. Details: `references/checks.md`.

## If time is short

Cut scope, never the rules. Keep, in this order: one golden scenario; the offline, sensitivity and clip checks; the
release guard and VERSION.txt. Then add: one seeded fault, the loop and fallback video, the soak (10 minutes rather
than none), more scenarios, a share build if a copy will be posted outside the demo area. Budget real time for waits
and discards: the worked example's plan for 7 golden runs and 10 seeded faults estimated about 10 hours from prep to
write-up, longer with discards.

## Common mistakes

| Mistake | What happened in the worked example | Fix |
|---|---|---|
| Rebuilt the released file name | An untracked output was rebuilt twice after upload, from uncommitted changes | Release guard and committed-tree builds |
| Controls inside a scrolling body | A control row was cut in 8 to 36 states | Controls as a footer outside the body; the clip check counts boxes |
| Removing an animation class on the parent's `animationend` | Four bars snapped full together | Keep the class until the LAST child animation ends; a frame-sampled check |
| Print HTML without embedded fonts | The booth card printed in a fallback serif with Type3 glyphs | Embed faces plus a symbols subset; PDF font check |
| Cleanup by name prefix | Two stacks from an earlier run were deleted, then restored | Delete only what the run's state names or tags |
| Redaction blind to escape codes and wraps | An internal name survived as a fragment at a line wrap | An escape-free second pass; fragments in the deny list |

All of them, with root causes: `references/pitfalls.md`.

## Red flags: stop

- "Edit out the hiccup", "re-run that part and splice it in", "a newer version is fine for turn 2".
- "The host cut it off, but the artifacts were already written."
- "The share build just hides the panel."
- "It looks fine on my machine" (with your brand fonts installed, at 1920x1080, in one theme).
- "Same version, small fix, just rebuild it."
- "Another team said the licence is fine."
- A number, caption or label on screen with no file you can name behind it.

## Rationalizations

| Excuse | Reality |
|---|---|
| "Visitors can't tell a splice." | Your colleagues can, from the timestamps and digests on screen. One found splice discredits every real run. |
| "The approval is the boring part; script it into the cut." | The approval is the product's control. Recreate it as its own labelled segment over the real handoff, or show it real. |
| "Length-preserving redaction is overkill." | A changed byte count breaks `.timing`; the replay garbles silently. |
| "We'll fix the PDF fonts on site." | The booth has no network and a borrowed laptop. Check the PDF's fonts before you print. |
| "The renderer is free." | Check its licence for your organisation. |

## Files in this skill

- `references/`: `capture.md`, `replay-format.md`, `replay-terminal.md`, `video.md`, `packaging.md`, `checks.md`,
  `pitfalls.md`.
- `scripts/` (Python 3 stdlib; Node 20+ with Playwright for the `.mjs`): `record_pty.py`, `redact_cast.py`,
  `cut_segment.py`, `scan_cut.py`, `release_guard.py`, `version_manifest.py`, `pdf_fonts_check.py`,
  `offline_check.py`, `clip_check.mjs`, `offline_check.mjs`. Each prints its usage with `--help` or no arguments.
- `templates/fonts-embedded-only.conf`.
- Related skills: `terminal-replay` (the replay), `demo-engine` (screen modes and staff panel), `booth-talk-track`
  (talk track and cheat sheet).

Not included on purpose: the worked example's data, prompts, rules files, staff code, account identifiers and its
replay app's source. Build your app on your own stack; the patterns above are what carries over.
