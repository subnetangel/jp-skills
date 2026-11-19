# Review passes before anything is shared

The scripts catch mechanical problems. People catch the rest. Run these passes on the built files (the share deck,
the talk-track page, the demo), not on the source, and keep each pass's findings in the checks file.

## 1. Design review

Someone who did not build it looks at every slide or screen, in both themes, at the presenter's real window size.

- One idea per slide; the headline states the claim; nothing competes with what the speaker says.
- Text fits its box at the real window size; nothing clipped, overlapping or under a caption.
- Contrast: body text 4.5:1, large text and strokes 3:1, in both themes.
- Numbers on slides match the figures file and the talk track exactly.
- Visual honesty: sample data, mockups and recreations are labelled on the slide.
- If no browser is available, say the design review was done from the source only and is not a visual pass.

Optional companions for HTML pages (third-party, install them yourself): Impeccable
([github.com/pbakaus/impeccable](https://github.com/pbakaus/impeccable), Apache-2.0) for a frontend polish and audit
pass, and Hallmark ([github.com/Nutlope/hallmark](https://github.com/Nutlope/hallmark), MIT) for a static page check.
Read their instructions before you run them; this repository does not ship them.

## 2. QA pass

Drive the artifact the way the audience or the staff will.

- Every key, click and link works; the share build has no notes; the presenter build's notes match the talk track.
- The offline check passes on the exact file being shared (`scripts/offline_check.py`: requests=0 local=0).
- The sensitivity and number-source checks pass on the exact file being shared.
- The timing line passes; the timing table matches the slide count and order.
- For demos: every mode, the reset, the staff panel, and one full hands-free loop.

## 3. Review loop

Iterate until a review finds nothing blocking, with a fixed cap so the loop ends.

1. A reviewer with **fresh context** (a new session or a person who has not seen the drafts) reads the artifact
   against the brief: audience, outcome, slot, the one message and the ask. Fresh context matters: a reviewer who
   watched it being written fills the gaps from memory.
2. Findings are sorted as **blocking** (wrong fact, missing ask, over time, hygiene hit, broken mechanic) or
   **advisory** (wording, order, polish).
3. Fix every blocking finding; take or decline each advisory one and say why.
4. Re-run the checks, then a new fresh-context review. Stop when a round has no blocking findings, or after three
   rounds; then list what is still open for the speaker to decide.

A structured version of this loop for documents is the Elephant-Goldfish Model
([github.com/google/elephant-goldfish-model](https://github.com/google/elephant-goldfish-model), Apache-2.0), a
third-party plugin with an iterating review skill. It is optional; the steps above work without it.

## 4. Humanize pass

Before the final review round, run the `humanize-pass` skill on all prose (slide text, notes, talk track, Q&A,
README) and keep its before/after log. Re-run the number-source check afterwards: a rewrite must not change a fact.
