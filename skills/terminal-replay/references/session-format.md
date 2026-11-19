# Session script format

A session script is one JSON file (YAML works when PyYAML is installed). `build_replay.py` validates it, and the
same object drives the HTML player and the video timeline.

## Top level

| Key | Type | Notes |
|---|---|---|
| `title` | string | Page title and the bar's title |
| `badge` | string | Default "Recreated, not live". The build refuses a badge that does not say recreated, replay, scripted or simulated |
| `label` | string | One sentence on what is real: "A scripted recreation with fictional data" |
| `footer` | string | Sources and the fiction notice |
| `prompt` | string | Shell prompt shown before typed commands, e.g. `"user@host:~$ "` |
| `timing` | object | `type_cps` (default 40), `enter_ms` (250), `line_ms` (70), `hold_ms` (1800, the wait before autoplay takes a choice) |
| `start` | string | First scene id (default: the first scene) |
| `forbidden_terms` | list | Terms the build refuses to ship; not embedded in the page |
| `scenes` | list | See below |

## Scene

| Key | Type | Notes |
|---|---|---|
| `id` | string | Unique |
| `stage` | string | Short label in the bar: "2 · Plan" |
| `caption` | string | One line under the terminal |
| `clear` | bool | Clear the screen when the scene starts |
| `events` | list | Played in order |
| `next` | string | Scene to play after this one when it has no choices |
| `choices` | list | `{label, kind, goto}`; `kind` is `approve`, `decline`, `inject`, `next` or `restart` |
| `auto` | string | The scene autoplay picks at a choice (default: the first choice) |

## Events

| Event | Fields | Time it takes |
|---|---|---|
| `type` | `text`, optional `prompt` | characters / `type_cps` + `enter_ms` |
| `out` | `lines`, optional `line_ms`, `cls` | one `line_ms` per line |
| `note` | `text` (an annotation, shown in italics with ›) | one `line_ms` |
| `pause` | `ms` | as written |
| `caption` | `text` (replaces the caption mid-scene) | 0 |
| `stage` | `text` (replaces the stage label) | 0 |
| `clear` | none | 0 |

Every time divides by the speed (`?speed=` in the page, `--speed` in the build). Under reduced motion, typed text
appears at once and the cursor stops blinking; the pauses stay so the pace still reads.

## Inline colour

`[[ok:text]]`, `[[warn:text]]`, `[[err:text]]`, `[[dim:text]]`, `[[em:text]]`, `[[cmd:text]]`. Colour never carries
meaning alone: put the word (matched, held, declined) inside the mark. Choice chips add a glyph per kind (✓ ✕ !).

## Validation

`build_replay.py --check` prints the timing table and exits 1 with a list of problems: duplicate ids, a `goto`,
`next` or `auto` that names no scene, an unknown event type or choice kind, a badge that hides the recreation.
