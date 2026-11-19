# Capture: real sessions in a test environment

Goal: one real, uninterrupted session per scenario that a stranger could audit from the files alone. Everything the
replay shows later comes from these files. In the worked example, one team recorded seven golden scenarios and ten
seeded-fault runs this way in one test environment, plus two real faults from earlier attempts.

## 1. Before any run

| Item | What to write down or prepare | How the worked example did it |
|---|---|---|
| Environment | A non-production test environment you own. Never a customer's or a shared production one. | One test environment for every run. |
| Identities | A read-only identity for every planning turn and every read; a separate admin identity used only to create, change and tear down fixtures; the human approver's own identity. | Planning turns ran read-only; admin was used only for fixtures. |
| Tags | One run tag on every resource you create (`project=…`, `ephemeral=true`, `run=<id>`). Teardown keys off it. | Every resource carried a project tag, an ephemeral tag and the run's date tag. |
| Inventory before | A read-only listing of the environment: everything you might create, and leftovers you expect to be empty. | A short script of list and describe calls, saved as `inventory-before.txt`. |
| Product version | Export the exact product build you will show (read-only, e.g. `git archive`) and record commit and version in the run folder. Re-check before each scenario; if the release moved, use the new head for the next scenario, never mid-scenario. | Each run folder held a commit-and-version file. |
| Clean agent home | A fresh, empty agent home per run: no personal tool servers, rules, hooks or other skills. Install only the product under test, the standard way. | The CLI's home variable pointed at a fresh copy of an empty template. |
| Staging | The visible opening prompt is one or two sentences a user would type. Facts the agent needs (rules file, paths, artifact folder) go into workspace files it finds on its own. Nothing in staging tells the product how to behave. | A rules file and a short notes file; a one-sentence prompt. |
| Pre-flight | Your own read checks that the fixture is what you think. Never a rehearsal of the product, so "passed the first time" stays true of the captured run. | Read-only checks of the fixture only. |

## 2. Record each turn on a pty

Record the terminal as bytes plus timing (`script -T timing -B io` format), not as video. Bytes can be redacted
length-preserving, searched, replayed with `scriptreplay`, and turned into replay data; pixels can't.

```bash
python3 scripts/record_pty.py --out raw/<run>/ --name turn1 --prompt-file prompts/<run>-turn1.md \
  --idle-regex '<what your CLI prints when it waits>' --quiet 120 --max 5400 \
  --boot 'Trust all tools=\r' --quit-keys '/quit\r' -- <your-cli> chat
scriptreplay -T raw/<run>/turn1.timing -B raw/<run>/turn1.io      # watch it back
```

- The driver types the prompt one character at a time, waits for idle plus `--quiet` seconds, then quits. It never
  types anything else. **The human approval is never typed by a script into the agent's terminal.** If the capture
  uses the product's own scripted test approver on tagged ephemeral targets, the cut shows a recreated approver
  pane, labelled as recreated (`replay-format.md`).
- The child runs in the driver's own session and process group. Some agent hosts reap processes that start a new
  session (`setsid`, `script`, `pty.fork()`); the worked example lost turns to this until the driver kept the CLI a
  plain child of one foreground call.
- Long waits: let the product hand back on its own terms, then type one plain continue line. Record each continuation
  as its own turn file and caption the real time on screen. That is not an interruption.
- Never overwrite a capture. `record_pty.py` refuses an existing recording.

## 3. The golden bar: clean runs only

A run is golden only if ALL hold. Any miss: discard the whole run (keep it under `raw/discarded-<run>/` with a
`DISCARDED.txt` saying why), fix the fixture or the staging, and rerun. Allow a fixed number of attempts per
scenario, then report what still blocks it.

| Rule | Why |
|---|---|
| No host or tool-window cut. A session the host ended is not golden, even if the product's artifacts look finished. | The visitor would see a run that never finished on its own. |
| No operator correction, no re-plan, no feedback typed mid-run. | A re-plan after the operator passes back an error is a different story from "it planned and passed". |
| The product's own gates pass the first time and every step completes. | |
| The product's recorded verdict is PASS, quoted with file and line. A finalizer's "status: pass" is not a verdict. | |
| **One product version per scenario.** Every turn of a scenario, and its cut, runs on one version. A scenario re-recorded on a newer version replaces the old one whole. Each scenario and each fault shows its own version on screen. | Behaviour changes between versions; a mixed cut shows a product that never existed. |

Failures that happen on the way are evidence, not waste. Keep every one with its raw output and an index (time,
kind, what failed as recorded, how the product handled it, raw path, cut path). Some make honest "real failure" cuts.

## 4. Seeded faults

Show what the product does when something is wrong, with real runs, not mock-ups.

- One realistic issue per run, on its **own disposable fixture**, in the test environment only. Same staging and
  the same short prompt as the golden runs.
- Record per fault: the exact seeding, where you expect the catch, where the product actually caught it, its
  verbatim words with file and line, whether it blocked, asked for approval or proposed a fix, and the outcome.
- Pick faults that are real and cheap. Drop candidates the platform handles itself or that can't be queued on demand,
  and write down why.
- A fault the product can't see before execution is still worth showing, labelled as such.
- If the scripted approver can't do what a fault needs, end the cut where the run ended. Don't fake the rest.

## 4b. Recording a real human approval

`record_pty.py` types only the prompt. A real approval is typed by the approver, at their own terminal, with their
own identity: they start `script -T approval.timing -B approval.io`, run the product's approval command, type the
decision, and exit. Redact and cut that pair like any other segment.

## 5. Redact, then scan

Work only on copies. The raw folder stays private, untouched, and out of git.

```bash
python3 scripts/redact_cast.py private/redact-rules.json raw/<run> redacted/<run>
python3 scripts/scan_cut.py redacted/<run> --deny private/deny.json --json redacted/<run>/SCAN.json
```

- Redaction in `*.io` is length-preserving, so `.timing` stays valid. A second pass works on the escape-free view,
  because a TUI prints some tokens in pieces with escape codes between them, or cuts them at a line wrap.
- Never touch a hex digest: plan digests and hashes are evidence. The redactor skips long digit runs that sit
  inside a hex run.
- Built-in rules: common cloud access-key shapes, long secret-like blobs, 12-digit numbers, IPv4, UUIDs. Your rules
  file adds your real identifiers, codenames, aliases, fixture prefixes, local paths and branch names.
- Screenshots and other binaries are never copied by the redactor; a person redacts them.
- The scan fails on any 12-digit number you did not allow, secret-like tokens, and your deny list (include fragments
  of each real identifier and codename). Run it on the cut, the app's data files and every built HTML.

## 6. Teardown and the inventory diff

- Delete **only what this run's own state names**, or a resource that carries this run's tag. Check the
  inventory-before list first. Never delete by name prefix alone: in the worked example a cleanup by prefix once
  deleted two stacks that belonged to an earlier run.
- Refuse to delete a target that doesn't carry this run's tag.
- After teardown, sweep by tag for stragglers.
- Run the inventory again and diff it with the before list. Report "identical" or every difference with its reason.
- Before any step that creates resources on someone else's instruction, check for a newer instruction (a stop or a
  hold may be waiting).

## What not to do

- Screen-record a "good" run and edit out the hiccups, or re-run one part and splice it in.
- Rehearse the product on the fixture before the captured run.
- Paste a real identifier, alias or codename anywhere outside `raw/` and `private/`.
- Commit `raw/`.
