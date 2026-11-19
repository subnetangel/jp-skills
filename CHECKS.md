# Release checks for this branch

Run on 2026-11-18 on a fresh clone. "PASS (static)" or "PASS (simulated)" says how a check ran; "NOT RUN" says why.

## Release gate

| Check | Scope | Result |
|---|---|---|
| Denylist, working tree | all 140 files, file names, and the XML inside the 4 sample `.pptx` files | **0 hits** |
| Denylist, new commits | `git log -p --format=fuller` on this branch's commits over `main`: added lines, author and committer fields, file names | **0 hits** |
| Denylist, lines this branch removes | the same log, `-` lines only: old wording this branch deletes (6 old wordings of a PowerPoint effect name, 1 personal name in a sentence) | 7 hits, all already on `main`; none added |
| Secret patterns, working tree | 11 patterns: cloud access-key ids, private-key headers, GitHub, chat-app and Google API tokens, `sk-` keys, JWTs, quoted password, secret, key and token assignments, secret-key variable names | **0 hits** |
| Secret patterns, new commits | the same patterns over the branch's `git log -p` | **0 hits** |
| Network listeners | search for wildcard binds, `listen(`, `--host`, `http.server`, `createServer` | **0 hits**; nothing in the repository runs a server |

The denylist itself (company, product, team and service names, internal tools and domains, personal identifiers,
12-digit numbers) is kept outside the repository, because publishing it would publish the terms. The gitleaks
scanner was not available on the build machine, so the secret scan used the pattern list above.

## Repository checks

| Check | Command | Result |
|---|---|---|
| Skill format, AGENTS.md and CLAUDE.md in sync, shared copies identical, SPDX headers, scripts compile | `python3 tools/check_repo.py` | `CHECK_REPO: PASS` (8 skills, 41 scripts) |
| Worked example | `bash examples/acme-ledger/build.sh` | `TIMING: ~5:50 of 15:00, 61% spare … PASS`, `UNSOURCED: 0`, sensitivity `clean` on 5 files, `OFFLINE … requests=0 local=0 … PASS` on 3 files, `TELLS: 0` |
| Original sample (Acme Upgrade Assistant) | README "Try the sample" commands from the previous version | `TIMING … 28% spare … PASS`, `UNSOURCED: 0`, sensitivity clean, offline PASS on 3 files |
| demo-engine example | `python3 build.py src/demo.src.html example/acme-ledger-demo.html --launchers`, `python3 offline_check.py …` | 59,119 bytes, one file; `requests=0 local=0 links=0 PASS (static)`; 8 launchers written |
| terminal-replay example | `python3 scripts/build_replay.py …`, `python3 scripts/offline_check.py …` | 20,222 bytes; main path ~12.6 s at speed 1; `requests=0 local=0 links=0 PASS (static)`; the JavaScript timing matches the Python timing scene by scene |
| Simulated DOM run | `node tools/dom_smoke.js` with jsdom installed outside the repository | `DOM SMOKE: 41 passed, 0 failed` (deck keys and notes, share build, demo modes, picker, theme, staff code, terminal branches, report tabs and zoom, idle return, wall loop and pause, replay page) |
| Staff code hash | the engine's SHA-256 against Node's crypto on 8 inputs | all match |
| Cheat-sheet checker | `bash skills/demo-cheat-sheet/scripts/test-check-sheet.sh` | `test-check-sheet: PASS` |
| Release guard | `python3 skills/terminal-replay-demo/scripts/release_guard.py --self-test` | `8 of 8 cases pass` |
| Redact and scan | a synthetic capture through `redact_cast.py` and `scan_cut.py` | length preserved, digest untouched, redacted copy `pass`, raw copy `fail` |
| Booth build | `build_booth_talk_track.py examples/acme-booth.json …` | exit 0; PDFs skipped (no Playwright) and reported as skipped |
| External links | every URL in the docs and install notes | 26 of 26 return HTTP 200 |
| Browser checks | `runtime_check.js`, `probe.mjs`, `clip_check.mjs`, `offline_check.mjs`, booth PDFs | **NOT RUN**: no browser on the build machine |
| PowerPoint rebuild | `build_pptx.py --preview` on the sample | **NOT RUN**: needs Playwright; only comments and licence headers changed in `scripts/pptx/` |
| Visual review | look at every slide and screen in both themes | **NOT RUN**: no browser |

## Licences, file by file

`licensee` and `reuse` were not on the build machine, so this list is by hand.

| Files | Licence |
|---|---|
| Every script in `skills/`, `templates/`, `tools/` and `examples/` (`.py`, `.js`, `.mjs`, `.sh`) | MIT, `SPDX-License-Identifier: MIT` in the header (41 files) |
| All markdown, JSON, HTML, CSS and SVG written for this repository | MIT, per `LICENSE` |
| `skills/presentation-coach/examples/pptx/*.pptx` | MIT, per `LICENSE` (built from this repository's template) |
| `CODE_OF_CONDUCT.md` | Contributor Covenant 2.1, CC BY 4.0, adopted as its authors intend |
| Third-party skills and libraries | none vendored; linked in `THIRD-PARTY.md` |
| Fonts, photos, video | none bundled |
