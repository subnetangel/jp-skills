# Golden cuts and the replay data

Two layers sit between the raw capture and the screen:

1. **The golden cut:** redacted casts with a small, logged set of edits, plus the product's artifacts. Still a real
   recording; `scriptreplay` plays it.
2. **The replay data:** a session script the replay terminal plays (the `terminal-replay` skill's format), written
   from the cut. Every line is the run's own; excerpting is the only edit.

## 1. Golden cut layout

```
demo-cut/
  golden/<scenario>/
    01-turn1.io  01-turn1.timing         # one pair per segment, in order
    02-approval.io  02-approval.timing   # a recreated pane, if any, is its own segment and is labelled
    03-turn2.io  …
    artifacts/                           # the product's reports and JSON, redacted (digests unchanged)
    ARTIFACTS.md                         # each report file, its kind, and the product step that wrote it
    RUN.md                               # label, product version and commit, source capture, gate results, verdict
                                         #   (file:line), replay minutes after trims, one line per segment edit
    SCAN.json                            # scan_cut.py verdict = pass
  faults/<fault-id>/                     # same layout, one per seeded fault
  failures/<name>/                       # real failures from earlier attempts, untrimmed
  durations.json                         # replay minutes per cut, after trims
  LABEL.txt                              # the banner text
```

A `RUN.md` reads, in short: the label; the product version and commit; the source capture and its redacted copy;
"Dry run: pass; blockers 0"; "Validation report: PASS (file:line)"; "Replay after pause trims: 23.0 min"; then one
line per segment, such as "`01-turn1` ← redacted turn1: banner added; synthetic names; pauses over 2 s cut, replay
7.5 → 7.4 min."

## 2. The only edits a cut may carry

Each edit is listed in `RUN.md`. Nothing else changes.

| Edit | Rule | Tool |
|---|---|---|
| Label banner | First line of every segment, e.g. "Recreated from a real run in a test environment · synthetic names". | `cut_segment.py --label` |
| Synthetic names | Same-length renames only, so byte counts stay valid. Better: give the real fixtures the demo's names before the run. | `cut_segment.py --names` |
| Pause trims | Any pause over 2 s becomes 2 s. Bytes untouched. Report the replay length before and after. | `cut_segment.py --max-gap 2` |
| Recreated approver pane | The human's approval as its own segment: a persona at their own terminal, typing the run's real confirm token, over the run's real handoff. It writes no approval record. | your own; label it |
| Contradicting lines | Where the agent's own text names the test harness (and so contradicts the persona), flag the replay times while building the cut, drop those lines in the replay data, and say so in the notes. | flag, then cut in the data step |

**Never edited:** results. A refusal, a stop, an error, a blocked step or a FAIL stays exactly as recorded.

## 3. Replay data: a session script per scenario

Write it in the `terminal-replay` format: scenes with a stage and a caption, `type`, `out`, `note` and `pause`
events, and choices (`approve`, `decline`, `inject`). Inline marks such as `[[ok:pass]]` colour a word; colour
carries meaning only together with the word, so a colour-safe mode can add a glyph.

Write the data with one generator script per scenario that reads the cut and cites its sources (cast and replay
time, artifact file) in its docstring, so a reviewer can check each line. Check on export: every choice target
exists, 2 to 4 choices per step, every caption under 25 words.

## 4. Excerpting rules

- Lines stay in their recorded order. A trimmed line or a skipped block shows as `…`.
- Booth trims may drop routine narration and collapse long tool output to `…`. They never drop a step, a gate, a
  hand-back, a failure, a finding or a verdict. Log every trim in a review file.
- Lines that only make sense with private context are cut, and the generator's docstring says so.
- A typed continue line between hand-backs is shown with a caption of the real time the next turn started.
- Numbers in captions trace to a source file; keep a per-run fact file and check that no number on screen is
  missing from it.

## 5. Timing: compressed, and said so

The replay plays at a readable speed, not real time (the worked example: typing 60 chars/s, prose 260 chars/s, 45 ms
per output line, a 3 s hold per step). A recorded run of 20 to 45 minutes after pause trims plays in a few minutes.

Keep real time visible where it matters: a tool's real duration from the run, and captions with the real time at
each turn start, the approval and each hand-back. Make the replay a pure function of time over the events, so the
live replay, stills and the video draw the same frame. `?speed=` speeds it up for checks.

## 6. Honesty labels

Say what is real and what is recreated, at the level where it changes. Patterns (write your own words):

| Where | Example text |
|---|---|
| Every cast segment | "Recreated from a real run in a test environment · synthetic names" |
| Whole demo | "Recreated from real runs in a test environment, with synthetic names. The approver's pane and the decline path are recreated." |
| A seeded fault, before approval | "A real run on its own disposable test fixture, with one seeded issue and synthetic names. Shown as recorded." |
| A fault past the approval | "…Shown as recorded; the approver's pane is recreated." |
| A real failure from an earlier try | "A real failure from an earlier try, with synthetic names. Shown as recorded; it stays a failure." |
| The approver tab | "approval recreated with a persona · the plan digest and times are the run's" |
| Every scenario and fault | its product version, e.g. "Real run with a seeded issue · v4.4.5" |
| A branch with no real run behind it (decline) | a "simulated" tag on the step |

Check every caption against what is on screen in that cut: in the worked example, fault captions said only "Shown as
recorded" on cuts that also contained the recreated approver pane, and the next version fixed them.
