# terminal-replay-demo

A skill for your agent (and a checklist for you) to build an honest offline booth demo of a CLI or agent product:
real sessions recorded in a test environment, replayed in a recreated terminal inside one HTML file, with looping
videos for screens that have no laptop.

## What you get

- **Honest by construction.** Only clean, uninterrupted runs on one product version become "golden". Failures are
  kept and can be shown, labelled as failures. Every recreated part (an approver's pane, a decline path) says so on
  screen. Nothing is spliced.
- **Visitors can drive it.** Click or type through each step, open the evidence files, inject a real fault and watch
  what the product did, scroll back.
- **It works anywhere.** One file per demo, everything inlined, no network, opens by double-click, runs on autopilot
  or with a presenter.
- **It ships safely.** A release guard that refuses to rebuild under a released name, a `VERSION.txt` with hashes,
  and checks for the problems the worked example actually hit.

## How to use it

1. Install this folder in your agent's skills folder (see INSTALL.md at the repository root), together with
   `terminal-replay` and, for the screen modes, `demo-engine`.
2. Ask your agent: "Use the terminal-replay-demo skill to plan a booth demo of <product> for <event>." It reads
   `SKILL.md` and the references it needs.
3. Before you start, settle with the right people: a test environment you own, with a read-only identity for the
   agent and a tag for every resource you create; and, if you want videos, the licence of your renderer
   (`references/video.md`).

## What's inside

| Path | What |
|---|---|
| `SKILL.md` | The method, quick reference, red flags |
| `references/capture.md` | Test environment, recording turns, the golden bar, seeded faults, redaction, teardown |
| `references/replay-format.md` | Cut layout, allowed edits, replay data, timing, honesty labels |
| `references/replay-terminal.md` | The terminal's look, Drive it and Watch it, scrollback, both themes |
| `references/video.md` | Loops and the fallback video, with or without Remotion |
| `references/packaging.md` | One offline file, one booth build and the optional share build, release guard, the staff package |
| `references/checks.md` | Offline, sensitivity, entry, clip, motion, soak, PDF fonts |
| `references/pitfalls.md` | What went wrong in the worked example and how each was fixed |
| `scripts/` | Recorder, redactor, cut builder, sensitivity scan, release guard, VERSION.txt writer, PDF font check, static and browser offline checks, clip check |
| `templates/fonts-embedded-only.conf` | Lay out without your installed brand fonts |

The scripts need Python 3; the two `.mjs` checks need Node 20+ with Playwright. No data, prompts, identifiers or
secrets from the worked example are included.
