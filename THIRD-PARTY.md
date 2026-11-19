# Third-party sources and notices

This repository's own code and text are under the licence in `LICENSE`. This page lists every person, project and
document the skills cite or point to, what this repository takes from each, and under what terms. Nothing listed
here is endorsed by, affiliated with or sponsored by its author or owner. All names are trademarks of their owners.

## People cited as public inspiration

The coaching lenses are this repository's own synthesis, written in its own words. They credit these authors'
public work as inspiration and do not reproduce their courses, books or methods.
`skills/presentation-coach/references/source-notes.md` lists the exact public pages read and the attribution limits.

| Who | Public source | What the skills take |
|---|---|---|
| Vanessa Van Edwards | [scienceofpeople.com](https://www.scienceofpeople.com) | The warmth-and-competence lens, as a prompt for the speaker; no text copied |
| Vinh Giang | [vinhgiang.com](https://www.vinhgiang.com) | Deliberate variation in pace, volume, melody, tonality and pause; no text copied and no paid course material used |
| Mark Manson | [3 Steps to Becoming Great at Anything](https://markmanson.net/3-steps-to-becoming-great-at-anything), [The 80/20 Principle](https://markmanson.net/80-20-your-life) | A prioritization lens for rehearsal; no text copied |

## Optional companion skills (linked, not copied, not bundled)

Install them from their publishers if you want them. Read their instructions and licences before an agent follows
them.

| Project | Link | Licence (as published) | Used for |
|---|---|---|---|
| Elephant-Goldfish Model | [github.com/google/elephant-goldfish-model](https://github.com/google/elephant-goldfish-model) | Apache-2.0 | An optional structured review loop (`presentation-coach/references/review-passes.md`) |
| Impeccable | [github.com/pbakaus/impeccable](https://github.com/pbakaus/impeccable) | Apache-2.0 | Optional frontend polish and audit for HTML decks and demos |
| Hallmark | [github.com/Nutlope/hallmark](https://github.com/Nutlope/hallmark) | MIT | Optional static check for HTML pages |
| humanizer | [github.com/blader/humanizer](https://github.com/blader/humanizer) | MIT | Inspiration for the `humanize-pass` pattern list, which is written in this repository's own words |
| Remotion agent skills | [github.com/remotion-dev/skills](https://github.com/remotion-dev/skills), listed at [skills.sh/remotion-dev/skills](https://www.skills.sh/remotion-dev/skills) | See the repository | The optional video path in `terminal-replay` (`remotion-create`, `remotion-captions`, `remotion-render`, `remotion-license`) |
| MotionSites web builder | [github.com/Motionsites-AI/claude-skill](https://github.com/Motionsites-AI/claude-skill) | Split: instructions MIT; examples and media owned by MotionSites with use limits | Not used by any skill here; mentioned only so users know its media terms differ |

## Libraries and tools the optional paths use (not bundled)

| Tool | Link | Notes |
|---|---|---|
| Remotion | [remotion.dev](https://www.remotion.dev/docs) | Its licence page ([remotion.dev/license](https://www.remotion.dev/license)) says: "Remotion is free to use for individuals and companies up to three people. Obtaining a Company License is required only for entities ineligible for the Free License." Check your own eligibility |
| skills CLI | [skills.sh](https://www.skills.sh/docs) | Installs the Remotion skills with `npx skills add remotion-dev/skills`; its docs say it collects anonymous install counts |
| Playwright | [playwright.dev](https://playwright.dev) | Optional browser checks (`runtime_check.js`, `probe.mjs`, `clip_check.mjs`, `offline_check.mjs`, `read_demo.py`, booth PDFs) |
| jsdom | [github.com/jsdom/jsdom](https://github.com/jsdom/jsdom) | Optional, for `tools/dom_smoke.js`; install it outside the repository |
| python-pptx, lxml, Pillow, numpy | their PyPI pages | Optional, for native PowerPoint builds and previews |

## Documents and formats

| Document | Link | Use |
|---|---|---|
| Agent Skills specification | [agentskills.io/specification](https://agentskills.io/specification) | The skill folder format every skill here follows |
| AGENTS.md | [agents.md](https://agents.md) | The instruction-file convention `AGENTS.md` follows |
| Wikipedia: Signs of AI writing | [en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) | Background for the humanize pattern list; no text copied |
| Contributor Covenant 2.1 | [contributor-covenant.org](https://www.contributor-covenant.org/version/2/1/code_of_conduct/) | `CODE_OF_CONDUCT.md` adopts it verbatim, as its authors intend, with the contact left as a TODO; the Covenant is licensed CC BY 4.0 |

## Quotations

Checked on this branch: the only verbatim third-party text is the two-sentence Remotion licence quote above
(attributed, with its link) and the Contributor Covenant (adopted as a whole under its licence). A search for
quoted passages of 25 words or more in every skill and agent file found none from a third party.

Changes made while porting these skills to this repository:

- The humanize checklist was rewritten in this repository's words; a reference to a second humanizer project was
  dropped because its public page could not be found.
- Worked examples taken from one team's internal demos were replaced with the fictional "Acme Ledger" product,
  and every internal name, identifier, path and link was removed.
- The demo-engine template and the terminal player were written new in plain JavaScript and CSS; no code was copied
  from any earlier demo.

## Assets

No fonts, photos or videos are bundled. `skills/presentation-coach/assets/icon.svg`, the inline SVG marks in the
templates and the sample PowerPoint files in `skills/presentation-coach/examples/pptx/` are this repository's own
work under `LICENSE`. The templates use the system font stack; if you embed a font, ship its licence file next to it.
