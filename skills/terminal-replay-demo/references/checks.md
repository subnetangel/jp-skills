# Checks before every release

Run all of them on the exact file you will upload, with only the embedded fonts available. Put them in one command
per surface and record each result with its numbers in a status file per version.

## 0. Lay out like a borrowed laptop

Point the browser at a fontconfig that hides your locally installed brand fonts, so the page can use only what it
embeds.

```bash
export FONTCONFIG_FILE=$PWD/templates/fonts-embedded-only.conf
```

## 1. Offline

Static, no browser: `python3 scripts/offline_check.py dist/Demo-v1.5.html` (requests=0 local=0). In a browser:
`node scripts/offline_check.mjs dist/Demo-v1.5.html --states states.txt --keys "ArrowRight*40,l,ArrowRight*40"`.
Pass: 0 requests other than the file, 0 failed loads, 0 page errors, 0 fonts failed.

## 2. Sensitivity

`python3 scripts/scan_cut.py dist/ app/data/ demo-cut/ --deny private/deny.json`. Pass: verdict pass on every built
HTML (the booth build, and the share build if you make one), the replay data and the cut. Also check that the
required honesty labels are in the file.

## 3. Entry: first builds animate in

Every screen whose first element animates must animate when entered forward, with no extra click, and must show its
final state at once under reduced motion. Press → from the previous screen's last build and sample the first
element's opacity every frame: it must start below 0.6 and end at 1. With reduced motion it must be 1 in the first
frame.

## 4. Clip checks at the presenter's real window size

`node scripts/clip_check.mjs dist/Demo-v1.5.html --states states.txt --scrollers ".tbody,.report" \
  --viewports <presenter's window>,1920x1080,1280x800 --modes "dark=,light=&theme=light"`

- **Use the presenter's real window,** not just 1920x1080. Ask for a screenshot of the browser on their laptop and
  read the viewport size.
- **Count scroll containers.** A box with `overflow: auto` that is not a designated scroll region is a clip: macOS
  hides scrollbars by default, so a control under its edge just looks cut. Only the regions you name in `--scrollers`
  may scroll.
- **Count control boxes, not only text.** A button half under a caption is cut even if its label's line box isn't.
- **Both themes,** plus colour-safe if you have it.
- Every state: each scenario's every step, each fault, decline, the end card, each chapter, the loop, an answer panel
  opened from each question chip.

Also run an overlap check (no control intersects content it doesn't contain) and a containment check (nothing
outside its card's padding box).

## 5. Motion timing

Where a sequence matters to the story (bars filling one by one, a gate lighting up after the plan), sample every
frame and assert order and spacing: entered forward, the bars fill one by one, in order, at least 80 ms apart, only
after the screen is fully visible, at the presenter's window size in both themes, plus a frame strip for a person to
look at.

## 6. Soak

A booth screen runs for hours. Run each locked playlist for 30 minutes, all at once, offline, and sample every 60 s:
JS heap after a forced GC, DOM nodes, the item playing, and timer drift from a 1 s interval. Pass: heap at the end
within +25% (or +8 MB) of the first full-loop sample, nodes within +25%, drift p99 under 250 ms and max under 1 s,
every item seen at least once, 0 page errors. Run a 10-minute attract soak too: in the worked example an early
attract mode froze about 11 s in, which only a timed run showed.

## 7. PDF fonts

`python3 scripts/pdf_fonts_check.py --allow <your faces> dist/package/Demo-v1.5/*.pdf`. Fails on a face outside the
list, on a Type3 font and on a PDF with no font.

## 8. The rest of the set (adapt as needed)

| Check | What it proves |
|---|---|
| Runtime | every chip reaches its scripted response; typing, branches, keys, mode switch, loop start and stop |
| Contrast | text 4.5:1, non-text 3:1, both themes, colour-safe |
| Untraced numbers | every number on screen traces to a source file |
| Links | every link in the single file resolves |
| Release guard | the guard's own test passes (`scripts/release_guard.py --self-test`) |
| Reproducible | two builds of one commit give the same bytes |
| Independent review | a QA pass and a design pass by someone who didn't build it, on a copy of the released file |

Say in your own status what was not checked: real projector legibility, the browsers you did not open, overlay
scrollbars on a real Mac.
