# Booth spec (JSON)

One file drives every output. Strings accept talk-track-page cue markup (`[pause]`, `[slow: …]`, `[soft]`,
`[click: …]`, `[point: …]`, `[move: …]`, `[act: …]`, `**anchor words**`).

## Top level

| Key | Notes |
|---|---|
| `title`, `subtitle`, `badge`, `footer` | Page heading, context line, red badge (default "Staff only. Do not show visitors."), sources line |
| `wpm` | Planning rate, default 120. `--wpm` overrides |
| `min_spare` | Fraction of each path's budget left unused, default 0.10. Build exits 3 below it |
| `forbidden_terms` | Codenames, customer names, banned product names. Refused on the page, print copy and card text |
| `allowed_long_ids` | 12-digit numbers that may appear (for example published documentation placeholders). Any other 12-digit number is refused |
| `spoken_only` | `{terms, lines: [{text, status}], intro, pointer}`. `lines` print only in the staff PDF; `terms` are refused on the HTML page and the card text (unless `card.staff_line` is true) |
| `spoken_only_held`, `spoken_only_held_note` | true when the owner holds the spoken-only line: it stays in the spec but goes in no output, the print copy included, and its terms are refused everywhere. The note replaces it (default: "on hold, don't say it until the booth lead tells you") |
| `for_label` | e.g. "For <demo> v1.2.0": stamped on the timing table, card text, card preview and checks. Put it in `subtitle`, `footer` and the cheat sheet's subtitle yourself. Pair with `--suffix -v1.2.0` for the file names |
| `cue_card` | talk-track-page cue card: `message`, `anchors`, `ask`, `reminders` |
| `beats` | Object of beat id → beat (below) |
| `paths` | List of paths (below), shortest first |
| `sections` | `{id, title, nav, intro, items, lead}`. `lead: true` renders before the paths (stance, path-picking questions); others render after the Q&A (situations, never-say) |
| `close` | talk-track-page close: `title`, `time`, `script` (put the reset here) |
| `questions`, `questions_intro` | `{q, a, confirm}`; `confirm: true` shows ⚠ |
| `rehearsal`, `rehearsal_title` | The drill, one string per timed step with what "good" sounds like |
| `timing_note` | Line under the timing table: which screen times are worst-case, where staff run long |
| `card` | Below |

Dollar amounts and dates (month-day, ISO, quarter-year) are refused everywhere; keep them out of the spec.

| `cheat_sheet` | Optional one-page sheet for anyone covering the station: `{title, subtitle, min_pt (9), columns (2), size_mm ([210, 297]), accent, blocks: [{title, paragraphs, items}], footer}`. Model it on the demo's own staff quick-start: what it is in one breath, the problem, how it works, where it runs, what it covers, what's in the demo (real vs recreated), say and never say, run the station. Spoken-only terms are refused on it |

## Beat

| Key | Notes |
|---|---|
| `title` | Short name shown on the page, card and timing table |
| `click` | Exact actions, comma-separated; each becomes one chip. Use the demo's own labels in quotes |
| `say` | Lines said before or without playback. Counted |
| `over` | Lines said while the screen plays. Counted, but overlap `screen_s` |
| `screen_s`, `screen_source` | How long the screen plays in this beat, and where the number comes from (measured, or file:line) |
| `clicks_s`, `wait_s` | Seconds for clicking, and for waiting on the visitor (an answer, a choice) |
| `cue` | Delivery cue markup, sparingly |
| `land`, `pace`, `source` | What the beat must land, the pace note, the evidence for every claim in it |
| `anchor` | true: Learn mode keeps the line sharp. One or two per path |
| `card` | `{click, say}`: the short version printed on the card front |

## Path

`{id, name, budget_s, beats: [ids], purpose, warmth, competence, exit, notes}`. `exit` renders as the transition
box (not counted). Put deviations from the source playbook in `notes` with the reason.

## Card

`{title, front_path, front_min_pt, back_min_pt, size_mm: [w, h], staff_line, back: [{title, items}]}`. The front is
`front_path`'s beats (their `card` text); the back is `back`. The preview PDF lays both sides out at the minimum
sizes and fails (exit 4) if either side overflows. The card text is for whoever lays out the final card.
