# Talk-track page

`scripts/build_talk_track.py` turns an approved talk track into a self-contained HTML page the speaker rehearses
from. The page is presenter-only: it carries notes, guardrails and cues that never reach the audience, and says so in
a red badge at the top. The SKILL.md method decides what is said and why; this file covers the page.

## When to use

- The speaker has a talk track (speaker notes, a script, or the speaking package) and wants something to rehearse
  from, to read on a second screen while presenting, or to print.
- After a review pass, to hand back the revised script in a form the speaker can practice with that evening.

Never use it for anything the audience sees. Do not send or publish the page; hand the file to the speaker.

## Workflow

1. **Collect the content** in the speaker's own words. Reuse the approved script verbatim; never invent lines, facts
   or stories. Proposed changes go into `proposal` blocks (dashed boxes), never silently into the script.
2. **Write the spec** (JSON, schema below). One segment per slide or no-slides segment. Give every segment a
   `purpose`, a `warmth` note (how the speaker shows they are on the audience's side) and a `competence` note (what
   earns trust), one sentence each. Mark one to three `anchor` paragraphs per segment: the lines to say exactly. Add
   cues sparingly (see "Cue markup").
3. **Build:** `python3 scripts/build_talk_track.py spec.json out.html` (`--wpm 130` changes the planning rate; the
   default 120 suits number-dense material). It prints spoken words and an estimate per segment; with
   `"timing": {"auto": true}` it fills the timing table.
4. **Check hygiene.** Put every term that must never appear in `forbidden_terms`; the build refuses to write the page
   if one appears (exit 2). Add `--forbid "a,b"` for more.
5. **Render and look:** open it in a browser, confirm the three modes work (Full, Script only, Learn) and no line is
   clipped. If you cannot render, say the page is visually unverified.
6. **Report** the path, the spoken-word total and estimated duration (labelled estimates), and the open items the
   speaker must confirm (⚠ answers, proposals).

## Spec schema

Top level (all strings accept the inline markup below unless noted):

| Key | Type | Notes |
|---|---|---|
| `title` | string | Used in the H1 ("Talk track: …") and `<title>` |
| `subtitle` | string | Audience, venue, date, slot, time budget |
| `heading`, `doc_title`, `badge` | string | Optional overrides for the H1, `<title>`, and the red badge |
| `how_to_use` | bool | Default true; the legend card. `method_note` overrides its last paragraph |
| `cue_card` | object | `message`, `anchors` (list of `{label, text}` or strings), `ask`, `reminders` |
| `segments` | list | See below |
| `close` | object | `title`, `time`, `script` (list of `{text, anchor}`) for a post-demo or post-Q&A close |
| `questions` | list | `{q, a, confirm}`; `confirm: true` prefixes ⚠. `questions_intro` overrides the lead line |
| `extra_sections` | list | `{id, title, intro, paragraphs, items}` cards, e.g. "If the projector fails" |
| `timing` | object | `{"auto": true, "budget_s": 330, "min_spare": 0.10, "note": "…"}` computes the table and a spare-time PASS/FAIL (default target 10% of `budget_s`; the script prints a `TIMING:` line); or `{"intro", "rows": [{segment, words, estimate, checkpoint}]}` to supply it |
| `rehearsal` | list | Drill strings; `rehearsal_title` overrides the heading |
| `footer` | string | Sources and the presenter-only statement |
| `forbidden_terms` | list | Build refuses if any appears (case-insensitive, whole word) |

Segment:

| Key | Type | Notes |
|---|---|---|
| `id`, `nav` | string | Anchor id (default `s<n>`) and the nav label (default the number) |
| `title`, `time` | string | Card heading and the right-hand time note |
| `purpose`, `warmth`, `competence` | string | One sentence each |
| `script` | list | `{"text": "...", "anchor": true}` paragraphs, or `{"proposal": "...", "label": "..."}` dashed boxes |
| `transition` | string | Rendered as the Transition box; counted as spoken unless `count_transition: false` |
| `notes`, `notes_title` | list, string | Collapsible guardrails under the card |
| `pauses_s`, `checkpoint` | number, string | Auto timing: seconds of pauses and clicks, and the clock checkpoint text |

`examples/acme-talk-track-spec.json` is a complete six-segment example with fictional content.

## Cue markup (inside any text)

| Write | Renders | Meaning |
|---|---|---|
| `[pause]` or `[pause: stop, look up]` | amber chip | A real stop, 1 to 2 s |
| `[slow]` or `[slow: for the comparison]` | blue chip | Drop the pace for the meaning |
| `[soft]` or `[soft: an invitation, not a sell]` | violet "softer" chip | Lower volume, warmer tone |
| `[click: the number]`, `[point: at the chart]`, `[move: toward the room]`, `[act: let the loop run]` | green chip | Mechanics |
| `[room]` or `[room: optional, skip if behind the clock]` | pink "ask the room" chip | A room moment: a show of hands, a quick bet, a question to the room |
| `**phrase**` | underlined | Anchor words; Learn mode keeps anchor paragraphs sharp and blurs the rest |

A script with a chip on every line reads as choreography. Keep the speaker's voice; do not reword a line to fit a cue.

## Room moments and humour beats

A room moment hands the room a small job: raise a hand, make a guess, answer one question. Use two or three in a
15-minute talk, at the points where attention usually drops (after the opening, before a demo, before the ask).

- Mark each one `[room: optional, skip if behind the clock]` and give it its own `pauses_s`, so cutting it is a
  decision the timing table already priced.
- Raise your own hand first, wait two seconds, look across the room and say what you see ("About half. Good.").
- Write a cold-room rule in the segment notes: if nobody moves, answer it yourself in one line and go on.
- Humour beats are optional and come from the speaker, not the script writer. Offer a light line as a `proposal`
  ("Optional, your call"), never as a required line, and drop it if it does not sound like the speaker on a good day.
  See the humour module in `coaching-modules.md`.
- Never aim a joke at the audience's tools, teams or past decisions.

## Spoken-word counting

Per paragraph, the build counts the words inside straight double quotes when the paragraph has them (stage
directions outside quotes are not spoken), otherwise the whole paragraph; chips and marks are removed first.
Transitions count unless `count_transition` is false. Duration = words / wpm + `pauses_s`. Present every figure as an
estimate and recommend a timed out-loud run; never call it measured delivery.

## Output

- `out.html`: one file, no external assets, works offline, prints cleanly (light theme, modes hidden).
- `--md out.md`: the same talk track as plain markdown, for review in a chat window or a print copy.
- Console: per-segment words and estimates, total, and the output path; or `REFUSED: forbidden terms present: …`
  (exit 2).

The warmth/competence and vocal-variety framing is a synthesis inspired by Vanessa Van Edwards' and Vinh Giang's
public teaching, as described in `source-notes.md`; it is not their method and should not be presented as such.
