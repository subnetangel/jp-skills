# Booth demo review checklist

Score every row PASS / FAIL / OPEN / N/A with evidence: a file:line, a probe result or a screenshot. A row you could run but only read is FAIL until run. **OPEN** means only the owning team can settle it (is it public today, what is the source): list it with the question, don't count it as PASS or FAIL. Timing rows (B2): time it by playing it hands-free with a clock, or estimate from step count × build time and say it is an estimate.

## A. Runs in the venue
| # | Check | How to verify |
|---|---|---|
| A1 | Opens by double-click from a local copy; no server | Open it from file:// |
| A2 | Zero network requests | `offline_check.py` prints requests=0 local=0; a network-off browser run when you can |
| A3 | No console or page errors through start, main moment and close | Browser console, or `probe.mjs` output |
| A4 | Works with keyboard and mouse only (no touch-only or hover-only controls) | Drive it with keys; key map per screen-modes.md §4 |
| A5 | Tells its story with no sound | Mute; captions or bubbles carry it |
| A6 | Package holds only deliverables: no raw captures, build scripts, or READMEs with real IDs | List the zip |

## B. Walk-up experience
| # | Check | How to verify |
|---|---|---|
| B1 | First screen asks the visitor something, or hooks with their problem | Screenshot of the load state |
| B2 | A 2-minute path exists and lands the main moment | Time it |
| B3 | Each moment needs one obvious action | Drive it cold |
| B4 | Ends with one clear next step for the visitor | Close screen |
| B5 | Reset for the next visitor as screen-modes.md §5 defines it | Code search: `idle`, Home/Esc; try it |

## C. Modes and staff
| # | Check | How to verify |
|---|---|---|
| C1 | Screen modes, staff entry and link options match screen-modes.md §1–3 (or each gap is listed by name) | Map control by control; a demo-engine build can run `tools/dom_smoke.js` |
| C2 | No demo key clashes with a key the shared map reserves (screen-modes.md §4) | Code search for `key ===` |
| C3 | A shortcut help screen on screen | Press `?` or the demo's help key |
| C4 | A staff cheat sheet exists (demo-cheat-sheet) | Check the package |
| C5 | Fallback: video or stills if the laptop fails | Check the package |

## D. Honesty and content
| # | Check | How to verify |
|---|---|---|
| D1 | Persistent label says what it is: mockup, simulation, replay of real runs | Every screen |
| D2 | Illustrative figures are badged where they appear | Search figures |
| D3 | Nothing confidential, roadmap or unreleased on screen unless the event allows it | Search "NDA", "planned", "roadmap" |
| D4 | No customer names or data, real account IDs (doc examples only), product prices or uncommitted dates. Story amounts (a fictional basket, savings) pass only if badged illustrative | Search 12-digit numbers, `$` |
| D5 | Every claim on screen has a source the staffer can name | Ask the owning team for any gap |

## E. Accessibility
| # | Check | How to verify |
|---|---|---|
| E1 | Honours reduced motion | `prefers-reduced-motion` in the CSS |
| E2 | Readable from 2 m: body text 18 px or larger at 1080p | Screenshot |
| E3 | Colour is never the only signal (PASS/FAIL also in text or icon) | Screenshot |

## F. Versions and shared folders
| # | Check | How to verify |
|---|---|---|
| F1 | The shared folder shows one current version: one subfolder per version, and only the current one has a plain name. Older versions sit in an Archive subfolder, or start with "zz Archive - " where they can't be moved, so they sort last | List the folder |
| F2 | `README - start here.txt` at the top names the current version and says which file to use for what (present, share, print, talk track, internal or customer) | Open it |
| F3 | `CHANGELOG.txt`, newest first: version, date and what changed, taken from the build notes. It is updated in the same step as each release | Its top entry matches the newest version folder and its VERSION.txt |
