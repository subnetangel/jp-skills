# One offline HTML file, one booth build, one package

## 1. One file that opens by double-click

The venue may have no usable network, and staff run the demo from their own laptops by double-clicking a downloaded
file. So:

- **Everything inlined:** JS, CSS, images and SVG as data URIs, every font as a base64 woff2 `@font-face`. The
  demo-engine template's `build.py` replaces placeholders such as `{{font:PATH}}`, `{{img:PATH}}` and `{{js:PATH}}`
  with inlined data. A bundled single-page app can be inlined by its bundler's single-file plugin.
- **Fonts embedded, never "installed":** a face referenced by name works on your machine and silently falls back on
  a borrowed laptop. Use a font whose licence allows embedding and ship its licence file.
- **No network:** no CDN, no analytics, no web fonts by URL, no `fetch`. Check with `scripts/offline_check.py`
  (static) and, when you can, `scripts/offline_check.mjs` in a browser (0 requests other than the file itself).
- **file:// works:** no service worker, no module imports from other files, and any link between files relative and
  checked. Prefer one file over two linked files.
- Size is fine: a file of several megabytes with every scenario, the fonts and a report viewer inside opens quickly.

## 2. One build for the booth; a share build only for copies posted elsewhere

**One build per demo that runs on autopilot or with a presenter.** Every station runs that file. Its staff controls
(modes, playlist, theme) sit behind a staff gesture, and the demo is visitor-safe on load. The demo-engine template
implements this.

**A share build is optional,** only for a copy posted outside the demo area. Build it from the same source and
remove, not hide, everything staff-only:

| | Booth build (every station) | Share build (copies posted outside the demo area) |
|---|---|---|
| Visitor-safe on load | yes | yes |
| Staff controls (staff panel, speaker notes, playbook) | present, behind a staff gesture | **removed from the file** |
| Staff code hash | present | **absent** |
| Spoken-only lines | never (they go in staff PDFs only) | never |

- The share build **fails if any staff marker survives:** the notes block, the panel ids, the code hash.
- Why the hash goes: a short code behind a hash in a widely shared file can be guessed in seconds. The staff code is
  a guard against visitors, not security.
- The staff code lives outside git (a mode-600 file, never printed). The build embeds only its hash. Never put a
  code or a hash in a skill, a README or a log.
- Anything meant to be said and not shown (unannounced plans, internal names) never enters any HTML, including
  hidden notes, because staff run that file on public screens. Put it in staff-only PDFs and make the build fail if
  it appears.
- Content that depends on a future launch is a build flag that is off by default, and the OFF build must not contain
  the words at all.

## 3. The release guard: never rebuild under a released name

What went wrong in the worked example: the built HTML in `dist/` was not in git, and it was rebuilt twice after the
upload, from uncommitted changes, under the released version's name. Anyone taking a hash from `dist/` got a build
nobody had checked.

The fix, in three parts:
1. `RELEASED.txt` lists every released file as `<sha256>  <name-vX.Y.html>`, appended when the upload is done
   (`scripts/release_guard.py record`).
2. Every script that writes an output refuses a path that carries a released version tag; `-dev` names pass and
   never ship.
3. The release build refuses an uncommitted source tree, so a hash can be reproduced from its commit. Two builds of
   the same commit must give the same bytes.

```bash
python3 scripts/release_guard.py --self-test
python3 scripts/release_guard.py dirty . app/src build || exit 1
python3 scripts/release_guard.py check dist/Demo-v1.5.html dist/package/Demo-v1.5/ || exit 1
# … build, check, upload …
python3 scripts/release_guard.py record dist/Demo-v1.5.html && git add RELEASED.txt && git commit -m "RELEASED: v1.5"
```

A fix after release is a new version, always.

## 4. The staff package

```
Demo-v1.5/
  Demo-v1.5.html             # the booth build
  Start-*.command, Start-*.bat   # double-click launchers per mode (demo-engine template)
  STAFF-QUICKSTART.pdf       # one page: open, keys, modes, reset, what to say if it fails
  BOOTH-CARD.pdf             # the 2-, 5- and 10-minute paths, likely questions (each path one page, 8 pt minimum)
  fallback-video.mp4         # the main run, full length
  loops/<playlist>-<theme>.mp4
  VERSION.txt                # version, build time, source commit, SHA-256 and bytes of every file, notes
```

Write VERSION.txt with `scripts/version_manifest.py`; staff compare the hash on their laptop with it. List each run
with the product version it was recorded on, what each loop plays and how to open the file.

Print PDFs from HTML in a headless browser. Embed the same faces as the demo, add a small symbols face for arrows
and check marks your brand font lacks, and run `scripts/pdf_fonts_check.py` on every PDF (see `checks.md`).

**Talk track and cheat sheet:** use the `booth-talk-track` and `demo-cheat-sheet` skills. They belong with the staff
material and never inside any HTML that a visitor can see.
