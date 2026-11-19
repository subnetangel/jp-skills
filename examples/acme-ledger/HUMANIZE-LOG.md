# Humanize log: this branch (newest first)

Run with `skills/humanize-pass`. Scanner: `python3 skills/humanize-pass/scripts/ai_tells.py` over every markdown and
JSON file in the repository (66 files) and the built HTML. First scan: `TELLS: 22`. After the edits below, the hits
left are the ones listed under "Kept on purpose".

| File and place | Before | After | Pattern |
|---|---|---|---|
| `examples/acme-ledger/QA.md`, question 7 | "The person who prepared the close doesn't approve their own plan; that's the same rule we use today." | "Who may approve their own work follows our existing approval rule, and I'll confirm that in writing." Marked ⚠. | Hard rule 2: the old line stated a rule with no source |
| `examples/acme-ledger/talk-track-spec.json`, s4 | "the controller looked at a plan and said no" | "the controller declined the plan at review" | Plain verb; matches the figures line word for word |
| `examples/acme-ledger/talk-track-spec.json`, s1 | "lost an evening to close week this year" | "lost an evening to close week lately" | A time claim with no source in a room moment |
| `examples/acme-ledger/talk-track-spec.json`, s1 and timing | "about ten minutes" | "about six minutes" | Fact check: the build's own estimate is 5:52 |
| `agents/bragi.md`, title and output format (9 lines) | "**Verdict** -- one paragraph: …" | "**Verdict:** one paragraph. …" | 5, dash connectors |
| `skills/presentation-coach/references/coaching-evidence.md`, 2 headings | "research — verified 2026-11-09" | "research (verified 2026-11-09)" | 5 |
| `skills/presentation-coach/references/coaching-validation.md`, heading | "validation — 2026-11-09" | "validation (2026-11-09)" | 5 |
| `skills/demo-best-practices/techniques.md`, table row | "Live landscape map" | "Live network map" | 6, stock word |

## Kept on purpose

- "High-leverage practice" (7 hits in `agents/bragi.md`, `presentation-coach/SKILL.md`, `persona-prompt.md`,
  `source-notes.md`, `README.md`): the name of the cited practice, kept as the source names it.
- "unlocked" and "Unlock" in the demo-engine README and staff panel: the literal state and button of the panel.
- "1 – 9" in the deck template's key help: a key range, not a connector.
- `skills/humanize-pass/SKILL.md` lists the tells on purpose and is not scanned.

## Not checked

The scanner finds patterns, not tone. A person still has to read the talk track aloud (REHEARSAL.md, drill 4).
