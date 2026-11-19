# Contributing

Thanks for helping. This repository holds portable agent skills for presentations, talk tracks and offline demos.
Please read this page before you open a pull request.

## Ground rules

- **Fictional and vendor-neutral.** Examples use clearly fictional products ("Acme Ledger", "Acme Upgrade
  Assistant"). No real company, product, client or person names in examples, no real figures, no personal paths,
  email addresses, internal URLs or identifiers.
- **Never invent facts in examples.** Every number in an example traces to a line in its figures file, and
  `untraced_numbers.py` must end `UNSOURCED: 0`.
- **No dependencies for the default path.** Scripts are Python 3.9+ standard library, or Node with no install.
  Browser-based checks (Playwright) stay optional, and a skill must still work with only file access and a shell.
- **No harness-specific tools.** Skills say "save the file" or "ask the user", never a tool that only one agent
  harness has.
- **Third-party work is linked, not copied.** Credit people and projects in `THIRD-PARTY.md`. Quote at most a short
  sentence with attribution; write everything else in your own words.
- **Plain writing.** Run the `humanize-pass` skill on new prose. Short sentences, no hype words.

## Before you open a pull request

```bash
python3 tools/check_repo.py                       # skill format, AGENTS/CLAUDE sync, shared copies, SPDX headers
bash examples/acme-ledger/build.sh                # worked example: TIMING PASS, UNSOURCED: 0, offline PASS
bash skills/demo-cheat-sheet/scripts/test-check-sheet.sh
python3 skills/terminal-replay-demo/scripts/release_guard.py --self-test
```

If you changed the deck template, the sample spec or a presentation-coach script, also run the sample in the README
("Try the sample") and, if you have Playwright, `node skills/presentation-coach/scripts/runtime_check.js` on both
builds. If you changed the demo-engine or the terminal player, rebuild their examples and, if you have jsdom,
`node tools/dom_smoke.js`.

Say in the pull request which checks you ran and which you could not run.

## Licence

By contributing you agree that your contribution is licensed under the repository's licence (see `LICENSE`). Add
`SPDX-License-Identifier: MIT` near the top of every new script.

## Conduct

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md).
