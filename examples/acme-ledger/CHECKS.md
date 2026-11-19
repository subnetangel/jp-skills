# Ready-to-present checks: Acme Ledger leadership briefing

Produced by `bash build.sh` (Python 3.9, standard library only) and the steps named in each row. Run on
2026-11-18. PASS means the check ran and its own output says so.

| Check | Result | Evidence |
|---|---|---|
| One message and one ask | PASS | Message: "Acme Ledger takes the matching work out of the month-end close, and nothing reaches the books until our controller says yes." Ask (slide 7 and the talk track): "Two more business units, for one quarter, with one controller as sponsor." |
| Evidence | PASS | `untraced_numbers.py … --figures FIGURES.md --allow allow.txt` ends `UNSOURCED: 0` (23 claims matched to a figures line; table in `built/numbers.md`) |
| Timing | PASS | `TIMING: ~5:50 of 15:00, 61% spare (target >= 10%): PASS` from `build_talk_track.py` (573 spoken words at 120 wpm plus pauses). Planned as about 6 minutes of talk and 9 of discussion |
| Hygiene | PASS | `sensitivity_check.py --config sensitivity.json` prints `clean` for the share deck, the talk-track page, the markdown talk track, `QA.md` and `REHEARSAL.md` (exit 0) |
| One file, offline | PASS (static) | `offline_check.py`: `requests=0 local=0 links=0 PASS` for `built/acme-ledger.html`, `built/acme-ledger-share.html`, `built/acme-ledger-talk-track.html`. A network-off browser run was not done (no browser on the build machine) |
| Deck size | PASS | 7 slides (10 or fewer); presenter build 50,259 bytes, share build 41,016 bytes |
| Share build | PASS | `build.py` refused nothing and the share file has no notes block; `tools/dom_smoke.js`: "share build has no notes" |
| Deck mechanics | PASS (simulated) | `tools/dom_smoke.js` with jsdom: 7 slides, → steps builds then slides, N opens the notes for the slide. `runtime_check.js` (Playwright) was not run: no browser on the build machine |
| Q&A | PASS | `QA.md`: 7 questions, hard ones first; 3 marked ⚠ (cost, bigger entities, the approval rule) and listed as open items |
| Rehearsal | PASS | `REHEARSAL.md`: 3 drills plus a timed run, each with what good sounds like, and the recall check |
| Prose | PASS | `ai_tells.py` on the markdown talk track, `QA.md`, `REHEARSAL.md` and `README.md`: `TELLS: 0`. Log: `HUMANIZE-LOG.md` |
| Visual review | NOT RUN | No browser on the build machine: no stills were rendered and nobody looked at the slides. Open `built/acme-ledger.html` in both themes at your window size before presenting |

## Open items for the speaker

- ⚠ A cost estimate with a source (question 4).
- ⚠ Which larger entity could join the next phase (question 5).
- ⚠ The approval rule for who may approve their own work (question 7).
- The optional story on slide 2 needs a true story from the speaker, or it stays out.
