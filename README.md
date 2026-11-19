# jp-skills: presentation and demo skills for any AI agent

Skills that help an AI agent build talks and demos the way an experienced presenter would: one message and one
ask, a talk track in the speaker's own voice with timing and delivery cues, likely questions with short answers, a
rehearsal plan, a single-file HTML deck that works offline, and walk-up demos with a staff panel and a recreated
terminal. Every number has to trace to a source, every talk has to leave at least 10% of its slot spare, and every
check reports pass, fail or not run with its evidence. Nothing here invents facts, stories or results.

The skills use the open [Agent Skills](https://agentskills.io/specification) format, so they work in Claude Code,
OpenAI Codex CLI, Cursor, Gemini CLI, GitHub Copilot and other harnesses (`INSTALL.md`). The default path needs
only Python 3.9 and a way to read and write files.

## What's inside

| Skill | Use it for |
|---|---|
| [`presentation-coach`](skills/presentation-coach/SKILL.md) | Build, review or rehearse a talk: one message and ask, slide-by-slide talk track, timing, Q&A, rehearsal, the HTML deck template, the rehearsal page, number, hygiene and offline checks, review passes, optional PowerPoint |
| [`humanize-pass`](skills/humanize-pass/SKILL.md) | Make prose read as written by its owner, with a scanner for common AI tells and a before/after log |
| [`booth-talk-track`](skills/booth-talk-track/SKILL.md) | What staff say at a walk-up demo: short timed paths, a staff page, a pocket card, a drill |
| [`demo-engine`](skills/demo-engine/SKILL.md) | Fill in the single-file offline demo template in `templates/demo-engine/` |
| [`terminal-replay`](skills/terminal-replay/SKILL.md) | A recreated terminal session as one HTML file, and optionally a video |
| [`terminal-replay-demo`](skills/terminal-replay-demo/SKILL.md) | Capture real terminal sessions honestly for a booth demo: golden runs, redaction, release guard, venue checks |
| [`demo-best-practices`](skills/demo-best-practices/SKILL.md) | Review a demo for the venue, with a checklist and shared screen modes |
| [`demo-cheat-sheet`](skills/demo-cheat-sheet/SKILL.md) | A one-page card for someone covering a demo they did not build |

Also: [`agents/bragi.md`](agents/bragi.md), a coach persona any harness can load as a system prompt;
[`templates/demo-engine/`](templates/demo-engine/README.md), the demo shell; [`examples/acme-ledger/`](examples/acme-ledger/README.md),
a complete worked example; [`tools/`](tools/), repository checks.

## Quick start

Install (details per harness in [`INSTALL.md`](INSTALL.md)):

```bash
git clone https://github.com/subnetangel/jp-skills.git && cd jp-skills
DEST=~/.claude/skills        # Claude Code. Codex: ~/.agents/skills · Cursor: ~/.cursor/skills
                             # Gemini CLI: ~/.gemini/skills · Copilot: ~/.copilot/skills · others: INSTALL.md
mkdir -p "$DEST" && for s in skills/*/; do cp -r "$s" "$DEST/"; done
cp -r templates/demo-engine "$DEST/demo-engine/template"
```

Then ask your agent, for example:

- "Review this deck against the presentation-coach skill: `<path>`. Audience: `<who>`. Outcome I want: `<what>`."
- "Build a 10-minute executive briefing from this brief, with a talk track and a rehearsal plan."
- "Use the demo-engine skill to make a booth demo of `<product>` that runs offline."
- "Turn this terminal transcript into a terminal replay with an approve and a decline branch."

First time: tell the agent your role, your usual audiences and your house rules (names that must stay out of
audience material), and copy `skills/presentation-coach/examples/sensitivity.example.json` to your own
`sensitivity.json` with your terms. Keep that file out of public repositories.

## Try the worked example

```bash
bash examples/acme-ledger/build.sh
```

It rebuilds the 7-slide Acme Ledger deck (presenter and share builds), the talk track (HTML and markdown) and runs
the checks: `TIMING: ~5:50 of 15:00, 61% spare … PASS`, `UNSOURCED: 0`, the sensitivity check, and
`OFFLINE: … requests=0 local=0 … PASS` for each file. Open `examples/acme-ledger/built/acme-ledger.html` and press
`?` for the keys, `N` for notes, `L` for the light theme. `examples/acme-ledger/CHECKS.md` lists every result.

The same story as a walk-up demo: `templates/demo-engine/example/acme-ledger-demo.html` (modes, staff panel with the
placeholder code `0000`, recreated terminal, report viewer) and as a terminal replay:
`skills/terminal-replay/examples/out/acme-ledger-replay.html`.

The original sample, the fictional "Acme Upgrade Assistant", is still in `skills/presentation-coach/examples/`
with prebuilt PowerPoint files; `skills/presentation-coach/references/deck-workflow.md` covers the native
PowerPoint build and its limits.

## Checks

```bash
python3 tools/check_repo.py          # skill format, AGENTS.md and CLAUDE.md in sync, shared copies, SPDX headers
bash examples/acme-ledger/build.sh   # the worked example's timing, number, sensitivity and offline checks
NODE_PATH=<dir>/node_modules node tools/dom_smoke.js   # optional: simulated-DOM run of the deck, demo and replay
```

Browser checks (`runtime_check.js`, `probe.mjs`, `clip_check.mjs`) are optional and need Playwright. A check that
could not run is reported as not run, never as a pass.

## Credits

The coaching lenses are inspired by the public work of **Vanessa Van Edwards** (warmth and competence),
**Vinh Giang** (pace, pause and vocal variety) and **Mark Manson** (high-leverage fundamentals and honest feedback).
The humanize pattern list draws on Wikipedia's "Signs of AI writing" page and on
[blader/humanizer](https://github.com/blader/humanizer). Optional companions: the
[Elephant-Goldfish Model](https://github.com/google/elephant-goldfish-model) for review loops,
[Impeccable](https://github.com/pbakaus/impeccable) and [Hallmark](https://github.com/Nutlope/hallmark) for HTML
polish, and the [Remotion agent skills](https://github.com/remotion-dev/skills) for video. Sources, licences and
what is taken from each: [`THIRD-PARTY.md`](THIRD-PARTY.md).

This project is not affiliated with or endorsed by any employer or company, or by the people and projects credited
above. All names are trademarks of their owners.

## Contributing and licence

See [`CONTRIBUTING.md`](CONTRIBUTING.md), [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) and
[`SECURITY.md`](SECURITY.md). Licensed under the MIT License; see [`LICENSE`](LICENSE).
