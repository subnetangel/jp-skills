# Changelog

Newest first.

## 2.0.0 (unreleased)

- New skills: `humanize-pass`, `booth-talk-track`, `demo-best-practices`, `demo-cheat-sheet`, `demo-engine`,
  `terminal-replay`, `terminal-replay-demo`. Each installs on its own in any harness that reads Agent Skills.
- New template: `templates/demo-engine/`, a single-file offline demo shell with modes, a staff panel, a recreated
  terminal, a report viewer, launchers, a stdlib build and an offline check.
- New worked example: `examples/acme-ledger/` (7-slide deck, talk track in HTML and markdown, figures, Q&A,
  rehearsal plan, checks, humanize log).
- `presentation-coach`: `offline_check.py` (static proof of 0 requests), `--md` markdown copy of the talk track, a
  `[room]` cue for room moments, review passes (design, QA, review loop), the humanize step, and tile labels used as
  context by the number check.
- Removed the reference notes that were drawn from a paid course. The skills now use only free public material.
- `INSTALL.md` for Claude Code, OpenAI Codex CLI, Cursor, Gemini CLI, GitHub Copilot and VS Code, and other
  harnesses, plus any agent that reads AGENTS.md.
- Open-source files: `THIRD-PARTY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, issue and pull
  request templates, SPDX headers on every script, `tools/check_repo.py`, `tools/dom_smoke.js`, `CHECKS.md`.

## 1.x

- Presentation coach skill, the Bragi persona, the single-file HTML deck template, the rehearsal page, the number,
  sensitivity and runtime checks, and native PowerPoint builds, with the fictional "Acme Upgrade Assistant" sample.
