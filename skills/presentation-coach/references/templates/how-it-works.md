# Story arc: technical "how it works" deep dive

**Use for:** engineers, architects or colleagues new to a system who need to understand it well enough to explain,
operate or extend it. 12 to 20 minutes of speaking, then questions; often demo-adjacent.
**One message pattern:** "X turns A into B through these steps, runs here, and you keep control at this point."
**Ask pattern:** a specific next step for the technical audience: try it on one case, review one module, build one
extension together.

Typical shape: 8 to 9 slides, about 12 minutes of speaking. Click-through builds carry most of the explanation, so
budget extra pause seconds per slide (8 to 12 s on dense slides) for clicks and looking.

| # | Slide | Purpose | On the slide | In the talk | Typical time |
|---|---|---|---|---|---|
| 1 | Title and plain opener | Give a cold room the whole idea in 20 seconds | Title, one-line description, an ambient preview of the loop | The idea in one sentence a newcomer could repeat | 0:30 |
| 2 | What it is | One sentence and one picture: input, the system, the result | Three cards: what comes in, what the system does, what comes out; flow particles between them | Read the picture left to right once | 1:00 |
| 3 | What it does today | Exactly what it covers, item by item, and how deep | A capability grid with honest depth markers per item, and a "next" column clearly labelled | Say where coverage is partial; never imply roadmap items exist | 1:30 |
| 4 | Under the hood | Where each part runs and what it reads or writes | An architecture diagram built in steps: the boundary, the agent, the core, the interfaces, the outputs | One build per component, each with "reads" or "writes"; no acronyms without a definition | 1:45 |
| 5 | One example, end to end | Make it concrete with real output from a real run | A step track; each step's actual artefact (file name, a count, a status) appears with its build | Narrate the run; stop at the gate and say who approves | 2:00 |
| 6 | What changes for the user | Translate mechanics into the user's week | Before / after rows | "Today ... with it ..."; land control | 1:00 |
| 7 | How it is rolled out | A repeatable adoption motion | 3 to 4 stages on a road with a moving marker; read-only stages coloured differently from change stages | Who does what at each stage | 1:15 |
| 8 | How it extends | One core, modules that plug in, and how a new module gets built | Core with sockets; a new module snapping in on a build; the steps to build one | Walk the build steps of a new module; show the empty socket first | 1:30 |
| 9 | The ask, then thanks | A concrete technical next step | The ask as 2 to 3 items; contacts | The ask word for word; open questions | 0:45 |

## What makes it land

- **Real artefacts beat adjectives.** On the example slide, show the actual output of a test run (a file name, a
  count, a status) and say where it came from. Put each figure in the figures file.
- **Read versus write, always.** Technical audiences trust a system when you say precisely what touches what.
  Colour-code read-only and change steps consistently on every slide.
- **Builds are the explanation.** One component per click; the talk track names each click (`[click: ...]`).
- **Light and dark.** Rooms differ; check both themes and a still of every build before presenting.

## Common failures

Starting with the architecture before the reader knows what the system is for. A capability slide that mixes shipped
and planned. A diagram with every box visible at once. Running the example slide from memory instead of from the
real output. Overrunning on slide 4 (put a checkpoint there).

## Likely questions to prepare

What permissions does it need, and where? What happens on failure halfway through? How is a module tested before it
is trusted? What does it log, and who can read it? How long does a new module take to build?
