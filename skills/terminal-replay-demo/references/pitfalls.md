# Pitfalls from the worked example's history

Each row: the demo version where it hit (v1 is the first release), what happened, the root cause, and the fix.

## Build and release

| Hit in | What happened | Root cause | Fix |
|---|---|---|---|
| v2 | The `dist/` HTML carried the released name but wasn't the released file: it was rebuilt twice after the upload, from uncommitted changes. | `dist/` not in git; nothing stopped a rebuild under a released name. | v4: the builder refuses a released name (listed in `RELEASED.txt`) and an uncommitted tree; local builds are named `-dev`. v6: every script that writes an output calls the release guard, and the guard has its own test. |
| v5 | The booth card PDF printed in a fallback serif face with uneven word spaces. | The print HTML asked for a brand face it didn't embed; the browser used Type3 outlines plus a system serif. | v6: the print HTML embeds the demo's faces plus a symbols subset for arrows and check marks, and a PDF font check fails any other face or a Type3 font. |
| v6 (before release) | A bold check mark was synthesised as a Type3 font. | The symbols face covered one weight only. | The symbols face covers every weight. |
| v3 | An installed-only face came first in the font stack, so layout differed on a laptop without it. | Font referenced by name, not embedded. | v4: dropped from every stack; every layout check runs with a fontconfig that hides installed brand fonts. |

## Layout and motion

| Hit in | What happened | Root cause | Fix |
|---|---|---|---|
| v3 | Restart, Auto-play and the progress bar were cut in 8 step-card states (QA), and cut or hidden under a pinned caption in 36 of 153 states (design review). | The controls row sat inside the card body, which scrolled. With hidden scrollbars a scrolled-off row looks cut. | v4: the controls row is a footer outside the body. The body never scrolls; it steps down a level until it fits. The clip check counts control boxes and treats any undeclared `overflow: auto` box as a clip. |
| v4 | The step card stayed at a smaller level than it needed and didn't step back. | It didn't re-measure from level 0. | v5: measure from level 0 on every render and every resize. |
| v3 (seen in the presenter's recording) | Four bars snapped full together instead of filling one by one. | The entry code removed the `.replay` class on the card's own `animationend`, which cancelled the bars' delayed fills. | v4: keep `.replay` until the LAST bar's animation ends. A check samples every frame at the presenter's window size. |
| v4 | Later builds flashed on re-entry after Home. | Builds were reset with transitions on. | v5: reset builds with transitions off. |
| v2 | The default attract mode froze about 11 s in. | The old chapter loop. | v3: the default loop runs the "all" playlist; a 30-minute soak and an attract soak were added. |

The animation fix, as a pattern:

```js
// before: the parent's own animationend removed the class, cancelling the children's delayed animations
el.addEventListener('animationend', function done(e) { if (e.target === el) { el.classList.remove('replay'); } });
// after: wait for the last child animation
const last = [...el.querySelectorAll('.pip i')].pop() || el;
el.addEventListener('animationend', function done(e) { if (e.target === last) { el.classList.remove('replay'); } });
```

## Capture and cut

| Hit in | What happened | Root cause | Fix |
|---|---|---|---|
| capture round 3 | Capture sessions were killed after 300 s. | The host reaps processes that start a new session; `script` and `pty.fork()` both do. | A pty driver that keeps the CLI in its own process group, with turns run as children of one foreground call. |
| capture round 4 | A session ended at the host's tool-window limit while the agent was still writing evidence. | Host limit. | Discarded from golden and kept as a catalogued fault. Plan long runs as several turns that use the product's own hand-backs. |
| capture round 3 | A missing client config made every in-environment check a blocker. | Capture setup, not the product. | Write a working config before turn 1 and check it read-only first. |
| first cuts | One sha256 was changed by the redactor. | A digit rule matched inside a hex run. | Never redact inside a hex run. |
| capture round 4 | An internal name survived redaction as a fragment the TUI cut at a line wrap; other names were printed in pieces between escape codes. | Rules saw the raw stream only. | A second pass on the escape-free view; fragments in the deny list. |
| capture round 4 | The agent's own text named the scripted test approver, which contradicts a persona approval. | The capture used a harness approver. | Flag those replay times while building the cut, drop the lines in the replay data, and say so. |
| capture round 4 | Cleanup by name prefix deleted two stacks that belonged to an earlier run; they were restored from saved templates. | Deleting by pattern. | Delete only what this run's state files name or what carries this run's tag; check the inventory-before list first. |
| v4 | Fault captions said "shown as recorded" on cuts that contain the recreated approver pane. | Caption written for the faults that end before approval. | v5: "Shown as recorded; the approver's pane is recreated." |
| v2 (writing the loop script) | The loop render left only the last item. | Rendering inside the concat-list loop. | Render all items first, then build the list. |
