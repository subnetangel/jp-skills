# Worked example: Acme Ledger leadership briefing

A complete talk built by following the skills in this repository, for a clearly fictional product. Acme Ledger,
its pilot and every number are invented for the example.

**Brief.** A finance operations lead asks the finance leadership team to extend a pilot. 15-minute slot, about six
minutes of talk, then discussion. One message: Acme Ledger takes the matching work out of the month-end close, and
nothing reaches the books until the controller says yes. One ask: two more business units for one quarter, with
one controller as sponsor.

| File | What it is | Made by |
|---|---|---|
| `FIGURES.md` | Every fact and its source, written first | by hand, `presentation-coach` section 4 |
| `talk-track-spec.json` | The spoken content: segments, cues, room moments, Q&A, rehearsal, timing | by hand, `references/talk-track-page.md` |
| `deck.src.html` | 7-slide single-file deck, from the template, notes written from the spec | `assets/deck-template.html`, `notes_from_spec.py` |
| `built/acme-ledger.html` | Presenter build (press N for notes) | `build.py` |
| `built/acme-ledger-share.html` | Share build: notes removed from the file | `build.py` |
| `built/acme-ledger-talk-track.html`, `.md` | Rehearsal page (Full, Script only, Learn) and a markdown copy | `build_talk_track.py --md` |
| `QA.md` | Likely questions, hard ones first, ⚠ on open facts | by hand |
| `REHEARSAL.md` | Drills, what good sounds like, the recall check | by hand |
| `CHECKS.md` | Every check, its result and its evidence | `build.sh` |
| `HUMANIZE-LOG.md` | Before and after for every prose edit in the humanize pass | `humanize-pass` |
| `sensitivity.json`, `allow.txt` | Sample forbidden terms and logistics phrases | by hand |

Rebuild and re-check everything with `bash build.sh`. Open `built/acme-ledger.html`, press `?` for the keys, `N`
for notes, `L` for the light theme.

For a walk-up version of the same story, see the demo-engine template's example
(`templates/demo-engine/example/acme-ledger-demo.html`) and the terminal replay
(`skills/terminal-replay/examples/out/acme-ledger-replay.html`).
