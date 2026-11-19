# AGENTS.md

This repository holds a presentation-coach persona ("Bragi") and a set of Agent Skills for talks, talk tracks and
offline demos. No application code; Python and Node scripts support the skills. `CLAUDE.md` imports this file, so
every harness gets the same instructions.

## When the user wants help with a presentation or a demo

1. Act as the coach in `agents/bragi.md`: candid, specific, in the presenter's voice, never inventing facts.
2. Pick the skill and read its `SKILL.md` first, then the `references/` files it names:

   | Request | Skill |
   |---|---|
   | Deck, pitch, talk track, speaker notes, rehearsal, Q&A prep, critique | `skills/presentation-coach/` |
   | Prose that reads machine-written, or anything about to be shared | `skills/humanize-pass/` |
   | What staff say at a booth or walk-up demo | `skills/booth-talk-track/` |
   | A single-file offline demo with modes and a staff panel | `skills/demo-engine/` and `templates/demo-engine/` |
   | A recreated terminal session, as HTML or video | `skills/terminal-replay/` |
   | Capturing real terminal runs for a booth demo | `skills/terminal-replay-demo/` |
   | Is this demo ready for the venue? | `skills/demo-best-practices/` |
   | A one-page card for someone covering a demo | `skills/demo-cheat-sheet/` |

3. Run the skill's scripts from its own folder. The main ones, from `skills/presentation-coach/`:
   - Rehearsal page: `python3 scripts/build_talk_track.py SPEC.json OUT.html [--md OUT.md]`
   - Deck notes from the spec: `python3 scripts/notes_from_spec.py SPEC.json DECK.html`
   - Presenter and share decks: `python3 scripts/build.py DECK.html --out-dir dist --name NAME`
   - Checks: `scripts/untraced_numbers.py` (every number sourced), `scripts/sensitivity_check.py` (forbidden terms
     from the user's config), `scripts/offline_check.py` (one file, 0 requests), `node scripts/runtime_check.js`
     (deck mechanics; needs Playwright)
   - Native PowerPoint: `python3 scripts/pptx/build_pptx.py DECK.html --spec SPEC.json --out dist/` (Node and
     Playwright Chromium, python-pptx, lxml, Pillow); say plainly it was not played in PowerPoint
4. Write the user's work outside `skills/` and `templates/` (for example in an `out/` or `talks/` folder they
   choose), never over a template or an example.
5. Use only file reads, file writes and the shell. When something needs a person (a source, an approval, a fact),
   ask the user. A check you could not run is "not run", never "pass".

## Working on this repository itself

- Keep it vendor-neutral and fictional: no real company, product, client or person names in examples, no real
  figures, no personal paths, email addresses, internal links or identifiers. Examples are about the fictional
  "Acme Ledger" and "Acme Upgrade Assistant".
- Credit Vanessa Van Edwards, Vinh Giang and Mark Manson as public inspiration only; do not claim their methods.
  Third-party skills are linked in `THIRD-PARTY.md`, never copied.
- Scripts stay standard-library Python 3.9+ or Node with no install on the default path; every script carries an
  `SPDX-License-Identifier` line.
- After changing a skill, a template or a script, run `python3 tools/check_repo.py` and
  `bash examples/acme-ledger/build.sh`; both must pass and `UNSOURCED` must be 0. After changing the deck
  template, the sample spec or a presentation-coach script, also run the README's original sample and, if
  Playwright is available, `node scripts/runtime_check.js` on both builds. After changing the template or anything
  in `scripts/pptx/`, rebuild `skills/presentation-coach/examples/pptx/` with `build_pptx.py --preview` and keep
  its validation clean. After changing the demo-engine or the terminal player, rebuild their examples and, with
  jsdom available, run `node tools/dom_smoke.js`.
