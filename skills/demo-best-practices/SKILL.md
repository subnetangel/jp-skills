---
name: demo-best-practices
description: Build, review or judge a booth, kiosk, demo-lounge or event demo (offline HTML, zipped kit, deck or video) against the venue it will run in, with evidence from running it. Includes a scored readiness checklist, a ranked list of interaction techniques, and a shared set of screen modes, keys and link options for every station. Use when asked whether a demo is "booth-ready", how to make a demo more interactive, or what a shared demo standard should contain.
license: MIT
metadata:
  version: "1.0.0"
---

# Demo best practices

What makes a walk-up demo work, drawn from a set of conference booth demos built by one team. **Core rule: judge
the demo against the venue it will run in, with evidence from running it, not from reading it.**

## When to use

- Reviewing a demo before an event, or critiquing a peer's demo.
- Choosing which interaction technique to add next.
- Drafting a standard so rotating staff can run any station (`screen-modes.md`).
- Not for the per-demo staff card: use `demo-cheat-sheet`.

## Procedure

1. **Get the venue facts first** and write them at the top of the review: network, input (keyboard and mouse, or
   touch), audio, screen size, staffed or unattended, how often staff rotate, what content is allowed (available
   today, or also preview). Defaults when unknown, stated as assumptions: no network, no speakers, keyboard and
   mouse, 1920×1080, staffed with rotation, available-today content only.
2. **Prove it runs offline.** Run `demo-cheat-sheet`'s static check, `python3 scripts/offline_check.py DEMO.html`
   (0 requests, 0 local files). If a browser is available, also open the file with the network off and watch the
   requests (`node scripts/probe.mjs` in `demo-cheat-sheet` does this with Playwright). Screenshot the start, the
   main moment and the close, and look at them. Say which checks you ran.
3. **Map the controls to the shared modes** in `screen-modes.md`: for each control the demo has, write the shared
   name or "no match", and list key clashes (a demo key that the shared map reserves, such as F, G, L, P or Esc).
4. **Score `checklist.md`.** One row each, PASS / FAIL / OPEN / N/A, with the evidence (file:line, check output or
   screenshot). No row passes on reading alone if it can be run.
5. **Pick techniques from `techniques.md`.** Rank by impact at a 2-minute stop, effort, and fit with the demo's
   honesty rules. Name what you reject and why.
6. **Report:** verdict in two sentences, the failed rows first, then the top three changes. Route facts you can't
   verify to the owner: **ask the owning team**.

## What the strong demos share

- **Picks before pitch:** the first screen asks the visitor a question (goal, industry, role) and the answer picks
  the path.
- **One action per moment:** "click anywhere to build", a pulsing hotspot, a callout with one Continue button.
- **Visible honesty:** a persistent label (mockup, simulation, recreated run), a per-item "illustrative" badge, and
  an "about this demo: what is real" screen.
- **Proof on screen:** counters driven by the run (changes made: 0, real durations), and the evidence one click away.
- **One file, shared modes:** modes, keys and link options follow `screen-modes.md`.
- **Silent by default:** captions carry the story; narration is optional.
- **A clean reset** for the next visitor (`screen-modes.md` §5).

## Lessons from one team's booth demo

- One self-contained HTML file that opens by double-click, zero network requests, fonts and media inlined.
- Open on the visitor's problem with industry examples, before how it works.
- Show only true recorded outcomes. Label anything recreated, and say it aloud.
- Ship it with a booth card (2-, 5- and 10-minute paths), a staff quick-start, a fallback video, and a version file
  with checksums.
- Keep each shared folder to one current version: a subfolder per version, older ones moved to an archive folder, a
  "README - start here" that names the current one, and a CHANGELOG updated with every release (checklist F1–F3).
- No prices, no dates, no customer names or data, no unreleased product names on screen.

## Common mistakes

| Mistake | Fix |
|---|---|
| "Works offline" from reading the code | Run the offline check, and a network-off browser run when you can |
| Treating live hardware or an API as the plan | Build the recorded path first; live is a bonus |
| A guided tour with no 2-minute path | Bookmarks or chapters for a 2-minute cut |
| Mock product screens presented as the product | Label them, or use real recordings |
| Raw captures or READMEs with real identifiers inside the posted package | Post only the deliverable files |
| Answering product questions from memory in the review | Mark them for the owning team |
| Every version's files loose in one shared folder | One subfolder per version, older ones archived, README names the current one, CHANGELOG says what changed |
| Archiving a folder because its name is old | Archive only when a newer version of the same deliverable exists |
| Copying an HTML demo inside a file-sharing service | Some services rewrite HTML on copy (metadata added, title changed), so the checksum no longer matches. Upload the file itself and check the posted copy's SHA-256 |
