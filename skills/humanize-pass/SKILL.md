---
name: humanize-pass
description: Run a humanizing pass on prose before it is reviewed or published, so slide text, speaker notes, talk tracks, demo screens, READMEs and web copy read as written by the person who owns them. Keeps every fact, number and name; removes AI tells such as not-X-but-Y contrasts, one-line closers, staged reveals, forced lists of three, dash chains, hype words and filler. Includes a stdlib scanner that lists likely tells by line and a before/after log format. Use when a draft sounds machine-written or before anything is shared.
license: MIT
metadata:
  version: "1.0.0"
---

# Humanize pass

Run this on every piece of prose before review or publication: slide text, speaker notes, talk tracks, demo
screens, alt text, READMEs, web copy. The goal is text that reads as if the owner wrote it on a good day. Beating
AI detectors is not the goal.

The pattern list below is this skill's own wording. It draws on the public "Signs of AI writing" page on Wikipedia
and on [blader/humanizer](https://github.com/blader/humanizer) (MIT), credited as inspiration; neither text is
copied here.

## Two hard rules

1. **Keep the meaning.** Every sentence still says what it said. Do not drop a claim, soften a commitment, or
   change a number, name, date, ranking or quote.
2. **Add no facts.** No new name, number, date, statistic, customer, quote or source, even one you believe is true.
   If a sentence needs a detail you do not have, write `[detail needed: what]` and list it in your report. Every
   number must still trace to the figures file.

## Leave alone

Code, commands, file paths, URLs, data tables, figures, quoted text, product names, and legal or compliance
wording. Keep the speaker's hygiene rules: the pass must not bring back a codename, an identifier, another client,
a price or an uncommitted date.

## Scan, strongest tells first

1. **Not X but Y.** "It isn't a tool, it's a platform." State the point. Keep a contrast only when it corrects
   something the audience actually believes.
2. **One-line closers and fragments.** "That's the real win." "No guessing. No waiting." Cut them, or fold them into
   a sentence that adds a fact.
3. **Staged reveals and run-ups.** "Here's the kicker:" "The result?" "So what does this mean?" Say the thing.
4. **Forced threes.** Three adjectives or three parallel items when the meaning has one or two.
5. **Dashes as connectors.** Use a period, comma, colon or parentheses. Aim for none in slide text and UI copy.
6. **Hype and stock vocabulary.** seamless, robust, leverage, unlock, empower, elevate, effortless, supercharge,
   delve, pivotal, crucial, landscape, tapestry, testament, underscore, foster, showcase, game-changer,
   world-class, next-generation. Use the plain word or the specific claim.
7. **Inflated significance.** "marks a pivotal shift", "sets the stage for". Keep the fact, drop the importance.
8. **Borrowed authority.** "Experts agree", "studies show". Name the real source from the figures file or cut it.
9. **Copula dodges.** "serves as", "stands as", "boasts". Use is, are or has.
10. **Shallow -ing tails.** "…, highlighting our commitment to …". Delete them.
11. **Filler openers and chatbot residue.** "In today's fast-paced world", "Let's dive in", "I hope this helps".
12. **Stacked hedges.** "could potentially possibly". Keep one hedge where the doubt is real.
13. **Formatting by habit.** Bold on every other phrase, "**Label:** sentence" bullets where prose would do, Title
    Case Headings, emoji bullets, a divider between every section.

One hit is a prompt to look closer, not proof. Act on clusters.

## How to run it

1. Read the whole file from disk, even if you wrote it this session.
2. Scan it: `python3 scripts/ai_tells.py FILE [FILE ...]`. It prints `file:line  pattern  match` rows and a
   `TELLS: N` line. It reads HTML and JSON as text and skips code blocks in markdown.
3. First pass: work down the list and rewrite flagged sentences in plain words. In a talk track, keep the speaker's
   voice: direct, first person, contractions are fine.
4. Second pass: scan again. Patterns 1, 2, 4, 5 and 6 survive most often.
5. Fact check: compare every number, name and date in the new text with the old. Any difference is an error unless
   a pattern required the cut.
6. Read it aloud, or at least read the headings and the first line of each section on their own. If they tell the
   story, the length is right.

## Log it

Keep a before/after log next to the deliverable (`HUMANIZE-LOG.md`), newest first, one row per real edit: file and
location, before, after, pattern number. End with the `[detail needed]` items and one line on what you did not
check. `examples/HUMANIZE-LOG.md` shows the format.
