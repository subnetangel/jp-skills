# demo-engine: a single-file offline demo shell

A working demo out of the box (the fictional product "Acme Ledger", 8 slides), built as ONE HTML file that opens by
double-click with no network. Vanilla JS and CSS, no dependencies, no build tools beyond Python 3.9.

```bash
python3 build.py src/demo.src.html example/acme-ledger-demo.html --launchers
python3 offline_check.py example/acme-ledger-demo.html     # OFFLINE: ... requests=0 local=0 ... PASS
```

Open `example/acme-ledger-demo.html`. Keys: → next, G slides, L theme, F full screen, Ctrl+Alt+S staff panel
(placeholder code 0000).

## What's in it

| Part | Where | Notes |
|---|---|---|
| Slide engine | `src/engine.js` | 16:9 stage that scales and centres; arrows, PgUp/PgDn, Space, click, swipe, 1-9, Home, End; `#N` per slide; counter; progress bar |
| Slide picker | G or the grid button | Hidden in kiosk and wall modes |
| Theme | `src/engine.css` | Light and dark token sets; L or the moon button; `?theme=`; saved per browser |
| Modes | `CONFIG` in `src/demo.src.html`, or the URL | `staffed` (default), `presenter`, `kiosk` (visitors drive, locked, idle return), `wall` (hands-free loop) |
| URL options | | `?mode=` `?playlist=` `?speed=` `?theme=` `?lock` `?idle=SECONDS` `?admin` `?reset` `#N` |
| Staff panel | `?admin`, the gear button, or Ctrl+Alt+S | Switch mode and playlist, jump to a slide, restart, reset the idle timer, switch theme, lock |
| Recreated terminal ("Drive it") | slide 4, `content/session.json` | The terminal-replay player: typing scaled by `?speed=`, approve and decline chips, an "inject an issue" branch, a "Recreated, not live" badge |
| Report viewer | slide 5, `content/report.json` | Human view and Machine view (JSON) tabs, scroll, zoom buttons, Ctrl+wheel, pinch, Esc closes |
| Launchers | `launchers/make_launchers.py` | `Start-Staffed`, `Start-Presenter`, `Start-Kiosk`, `Start-Wall` as macOS `.command` and Windows `.bat` |
| Checks | `offline_check.py`, `../../tools/dom_smoke.js` | Static 0-request proof; optional simulated-DOM run of keys, modes, chips, report and staff panel |

### Modes

| Mode | Who drives | On screen | Idle |
|---|---|---|---|
| `staffed` | staff and visitors | everything | back to the first slide after `idleSeconds` |
| `presenter` | the presenter, keys or a clicker | counter only; nav buttons appear on hover or focus | never |
| `kiosk` | visitors (keys, click, swipe) | no staff controls, no picker, no theme switch | back to the first slide |
| `wall` | nobody | the loop and a Pause control | a paused loop resumes |

The wall loop always starts at the first item of its playlist and plays the list in order. Keys do nothing in the
loop except P (pause) and the staff chord.

### The staff code is not security

The staff panel asks for a code so a visitor at a booth does not switch the demo into another mode by accident.
That is all it does. The file is a web page: anyone who has it can read every slide, every note and the hash in
`CONFIG`. A short code behind a hash can be guessed in seconds. Never put anything behind the panel that a visitor
may not see.

The code itself is never stored. `build.py` writes only its SHA-256 into `CONFIG.staffCodeSha256`:

```bash
printf '%s\n' 'your-code' > ~/.config/demo-staff-code && chmod 600 ~/.config/demo-staff-code   # outside git
python3 build.py src/demo.src.html dist/my-demo.html --staff-code-file ~/.config/demo-staff-code
# or: python3 build.py src/demo.src.html dist/my-demo.html --ask-staff-code
```

Without either option the build uses the placeholder `0000` and prints a note. Tell staff the code in person, not
on a printed card or in chat. `?reset` forgets an unlocked panel in that browser tab.

## Re-skin it (tokens only)

Every colour is a CSS variable in the two token blocks at the top of `src/engine.css`. Change those and nothing
else: the slides, the overlays and the terminal follow.

```css
[data-theme="dark"]  { --bg:#101418; --surface:#181e24; --accent:#ff9f43; --accent-text:#1a1000; /* ... */ }
[data-theme="light"] { --bg:#fffaf3; --surface:#ffffff; --accent:#b45309; --accent-text:#ffffff; /* ... */ }
```

Keep text at 4.5:1 against its surface and strokes at 3:1 in both themes. For a brand font, put the `.woff2` and its
licence file in `content/fonts/`, add `@font-face{font-family:Brand;src:url({{font:content/fonts/Brand.woff2}})}`
to `engine.css`, and set `--sans`. Use a font whose licence allows embedding (for example the SIL Open Font
License) and ship its licence file with the demo. The sample uses the system font stack, so it embeds no font.

## Make it yours: 10 steps

1. Copy the whole `demo-engine` folder next to your talk. Work in the copy.
2. Write your figures file first: replace `content/FIGURES.md` with one line per fact and its source.
3. Edit the slides in `src/demo.src.html`. Keep the `<section class="slide" data-title="…">` pattern; the title
   feeds the picker and the staff panel. Every number on a slide must have a line in your figures file.
4. Replace `content/session.json` with your own session script (format: the terminal-replay skill's
   `references/session-format.md`). Keep the "Recreated, not live" badge.
5. Replace `content/report.json` with your own report (title, summary, sections with columns and rows).
6. Set the defaults in `CONFIG`: mode, idle seconds, playlists and dwell time.
7. Re-skin through the tokens in `src/engine.css` only.
8. Pick a staff code, keep it in a file outside git, and build with `--staff-code-file`.
9. Run `offline_check.py` on the built file (requests=0, local=0), run your sensitivity check on it, and if you
   can, `tools/dom_smoke.js` adapted to your slides.
10. Open the built file by double-click on the laptop you will use, in each mode, in both themes, with reduced
    motion on; try every launcher once; then write a VERSION file with the file's size and SHA-256.

## Limits

- The launchers were generated and read here but not run on a real Mac or Windows machine. Try each one before
  the event. Leave a kiosk window with Alt+F4 or Cmd+Q.
- The checks in this folder are static or simulated. Look at the demo in a real browser at the presenter's window
  size before you call it ready.
- Video: `{{video:PATH}}` inlines an MP4 or WebM as a data URI. Large videos make a large file; keep them short.
