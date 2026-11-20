# ArtCraft suite: local tooling and headless MCP

This is a routing and verification runbook for the [17 official Crafting Apps](https://getartcraft.com/apps), not an assertion of desktop feature parity. A Linux x86-64 smoke pass exercised 16 apps' local outputs and one app's read-only discovery. The versions are reproducibility pins from the test, not a guarantee they are still current. Start with a synthetic fixture on each new build or platform.

## Route the job

| App and tested version | Choose it for | Firsthand Linux evidence |
| --- | --- | --- |
| [PhotoCraft](https://github.com/storytold/photocraft) 0.23.1 | Pixel editing, layered stills, masks and thumbnails | Scoped CPU headless MCP; exported a synthetic PNG. |
| [VectorCraft](https://github.com/storytold/vectorcraft) 0.24.1 | Logos, icons and reusable vector illustration | SVG parsed; expected elements and colors present. |
| [FilmCraft](https://github.com/storytold/filmcraft) 0.20.1 | Video assembly, timing and audio/video delivery | Scoped headless MCP; decoded two-cut portrait H.264/AAC export. Workflow below. |
| [LightCraft](https://github.com/storytold/lightcraft) 0.21.1 | Photo library, RAW development and photographic exposure/color | +0.5 exposure adjustment and decoded 80×48 PNG via CPU fallback. |
| [PdfCraft](https://github.com/storytold/pdfcraft) 0.21.1 | Inspect, edit, assemble or split an existing PDF | Opened and edited a synthetic PDF; page and metadata inspected. |
| [EffectCraft](https://github.com/storytold/effectcraft) 0.24.1 | Compositing, title cards, motion graphics and VFX | Created solid/text comp, visually checked PNG and fully decoded 1 s H.264. No VFX fidelity claim. |
| [AniCraft](https://github.com/storytold/anicraft) 0.2.1 | Frame-based 2D vector animation | Rendered PNG frame and exported a decoded 12-frame animated GIF with CLI. |
| [DesignCraft](https://github.com/storytold/designcraft) 0.20.1 | Page layout, posters, print and publications | Created document and text frame; decoded 200×120 RGBA PNG. |
| [FigCraft](https://github.com/storytold/figcraft) 0.18.1 | UI mockups, design systems and prototypes | Exported decoded 360×640 PNG. |
| [TextureCraft](https://github.com/storytold/texturecraft) 0.6.1 | Paint or bake textures against a 3D mesh | Decoded preview and 15 texture-map PNGs. |
| [MaterialCraft](https://github.com/storytold/materialcraft) 0.4.1 | Generate procedural/PBR textures without a mesh-editing workflow | Created graph and decoded six 32×32 map PNGs. |
| [SoundCraft](https://github.com/storytold/soundcraft) 0.20.1 | Audio editing, mixing, stems and sound design | Bounced 2 s of synthesized demo; decoded stereo PCM 48 kHz/16-bit and verified non-silent samples. |
| [WordCraft](https://github.com/storytold/wordcraft) 0.18.1 | Flowing text, documents and reports | Synthetic document and text/PDF export checked. |
| [DeckCraft](https://github.com/storytold/deckcraft) 0.18.1 | Slide-first story or presentation | PPTX structure/content and PNG preview checked. |
| [CADCraft](https://github.com/storytold/cadcraft) 0.20.1 | Dimensioned geometry and technical drawings | Created closed rectangle and parsed SVG geometry. |
| [GridCraft](https://github.com/storytold/gridcraft) 0.19.1 | Tables, formulas and spreadsheet models | Recalculated a formula to 42 and checked CSV content. |
| [Craft Anything](https://github.com/storytold/craft-anything) 0.6.1 | Scoped software exploration/build work, not media editing | In a projectless clean room: MCP initialize, list, ping and read-only toolset listing; no build, project study, provider or plugin exercised. |

For an ordinary reel: prepare stills in PhotoCraft (LightCraft for photo development); design reusable marks in VectorCraft; build titles/composites in EffectCraft and frame animation in AniCraft when needed; mix in SoundCraft; assemble and deliver in FilmCraft. Use PBR or CAD tools only when the shot needs them. Do not route still editing to Studio simply because it is branded ArtCraft.

**Separate products, not two extra verified editing engines.** [ArtCraft Studio](https://github.com/storytold/artcraft/releases/tag/artcraft-v0.41.1) is the AI image/video UI. Linux 0.41.1 launch did not reach its GUI because WebKitGTK/JavaScriptCoreGTK 4.1 libraries were missing. [ArtCraft Launcher](https://github.com/storytold/craft-launcher/releases/tag/v0.19.2) manages installations; its 0.19.2 CLI returned a version, but the desktop attempt did not show a window (Mesa/X11 shared-memory errors). No Studio or Launcher MCP, account, generation or GUI readiness was established. Don't infer MCP support from the suite's branding.

## Install, pin and qualify

1. Follow the official app's GitHub release page. Pin tag, exact asset name, OS/architecture, SHA-256, extraction method and invoked binary version in the run receipt. Compare to the tag's official checksum manifest and the release asset digest when available. Verify a trusted publisher signature separately when required; a manifest check alone is not signature verification. Do not fall back to repacks or pipe installers into a shell.
2. A Linux tarball can be inspected and safely unpacked without root. For a `.deb`, use `dpkg-deb -x package.deb ./package` (extraction, not system installation). For a verified AppImage on a no-FUSE host, use `./package.AppImage --appimage-extract` from an isolated, job-local package directory. Packaging varies: inspect for `bin/<app>-cli`, `usr/bin/<app>-cli`, or a wrapper that sets its library/data locations. PhotoCraft's tested AppImage entry is `AppRun --cli mcp --no-gpu`; FilmCraft's tested AppImage entry is its extracted `usr/bin/filmcraft-cli mcp`.
3. Inspect that exact binary's `--version`, `--help` and `mcp --help`. When an official binary is absent, inspect the tagged upstream source, license, toolchain files and lockfile; build the named CLI target with pinned dependencies in a separate build sandbox. For FilmCraft, upstream documents `cargo build --release -p filmcraft-cli`; prefer `--locked` with a compatible lockfile and check that tag's native prerequisites. Never assume CLI target names, flags, runtime assets, or MCP schemas are shared. Browser/WASM, Windows, macOS and other Linux architectures need their own test; never copy a Linux executable to them.
4. Keep tool definitions portable: build/install the binaries for the runner, then register an absolute path to its local wrapper in an MCP client that actually supports custom stdio servers. The wrapper is not itself a cloud connector. Do not distribute host paths, credentials or production data. Do not point clients at a desktop bridge as a silent fallback.

Example verification, performed in a directory with the pinned release's downloaded asset and manifest:

```sh
asset='filmcraft-0.20.1-linux-x86_64.AppImage'
LC_ALL=C awk -v name="$asset" '
  NF == 2 { file=$2; sub(/^\*/, "", file); if (file == name) {print; n++} }
  END {if (n != 1) exit 1}
' SHA256SUMS.txt > selected.sha256 &&
sha256sum --check --strict selected.sha256
```

## Scope the tool, then test it

- Use fresh read-only inputs and a separate writable output directory. Mount packages and necessary runtime libraries read-only. Give the subprocess an empty/minimal environment and temporary home; no account tokens, SSH agent, desktop sockets, live projects, broad user-directory mount or production destination.
- Use supported application roots if available, and enforce an OS sandbox where required. Tested root spellings: Photo/Effect/Sound/Design use `--automation-read-root DIR --automation-write-root DIR`; Material uses `--read-root DIR --write-root DIR`. EffectCraft and SoundCraft rejected explicit out-of-root writes in the probe. On FilmCraft, `--data-dir` only relocates FilmCraft data; it does not restrict unrelated reads/writes. The smoke run used Bubblewrap mount confinement and separately showed that an existing path outside those mounts could not be imported.
- Filesystem scoping is not network isolation. For sensitive tasks require an independently verified network-deny layer (e.g., isolated container with networking disabled or a managed sandbox). Linux network namespaces may be unavailable; do not turn a failed isolation check into unconfined execution. Do not start listeners, bridges, plugins, macros/scripts, accounts or generators just to make an export work.
- Speak MCP JSON-RPC over stdio: send `initialize` with the client's supported version, validate `serverInfo` and negotiated protocol, send `notifications/initialized`, then `tools/list` (including any pagination). Use returned tool schemas, correlate response IDs, keep stderr separate, check both top-level errors and tool `isError`, and distinguish text containing JSON from `structuredContent`. Cap time, memory, frame count, resolution and disk output. Close stdin and reap the process; handle timeout/cancellation without leaving a writer.
- Record which calls actually ran and validate decoded output independently. A handshake or tool listing alone is not readiness, project save is not render proof, and a zero exit with offline placeholders is not deliverable output. For files that overwrite without asking, choose unique names under a fresh job root or require explicit approval. Review metadata/licensing and never publish/upload automatically.

Minimal client entry (adapt key placement to the chosen client):

```json
{"mcpServers":{"filmcraft-headless":{"command":"/absolute/path/to/scoped-filmcraft-wrapper","args":[]}}}
```

## FilmCraft: verified edit, inspect and export

In the proof, the wrapper ran the tagged app in a fresh Bubblewrap filesystem namespace: read-only `/usr` with distro-appropriate library links, read-only extracted package at `/opt/filmcraft`, staged sources at `/work/inputs` (read-only), writable `/work/outputs`, temporary `/tmp`, minimal `/proc`/devices, cleared environment and no inherited credentials. The exact **in-sandbox** launch command was:

```sh
/opt/filmcraft/usr/bin/filmcraft-cli mcp --data-dir /work/outputs
```

A mount-scoped launcher, adapted from the Linux proof (usrmerged Linux; add a verified network-deny layer for sensitive inputs). Lay out the extracted AppImage in `package/` beside the wrapper and stage `inputs/` and `outputs/` before launch:

```sh
#!/bin/sh
set -eu
base="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
test -x "$base/package/usr/bin/filmcraft-cli"
test -d "$base/inputs"
test -d "$base/outputs"
exec bwrap --unshare-user --unshare-pid --die-with-parent --new-session \
  --clearenv --setenv HOME /tmp --setenv PATH /usr/bin --setenv LANG C.UTF-8 \
  --ro-bind /usr /usr --symlink usr/lib /lib --symlink usr/lib64 /lib64 \
  --ro-bind "$base/package" /opt/filmcraft \
  --ro-bind "$base/inputs" /work/inputs --bind "$base/outputs" /work/outputs \
  --proc /proc --dev /dev --tmpfs /tmp --chdir /work \
  /opt/filmcraft/usr/bin/filmcraft-cli mcp --data-dir /work/outputs
```

Use the pinned Linux x86-64 asset `filmcraft-0.20.1-linux-x86_64.AppImage` (tested archive SHA-256 `4a25aecb2e9481b65e7353528bca9e4a8c5388dd55f1486ffe64502e08bdfa02`); verify against the official manifest before extracting. No device acceleration, desktop file dialog, control port or GUI was required. Don't treat a namespace that only scopes mounts as disabling the network.

FilmCraft 0.20.1 returned `command_batch`, `command_list`, `command_run`, `doc_inspect`, `media_import`, `project_inspect`, `render_frame`, `render_preview`, and `sequence_inspect`, plus `ui_click`, `ui_control`, `ui_drag`, `ui_elements`, `ui_inspect`, `ui_key`, `ui_screenshot`, `ui_type`. Only the relevant headless engine calls below were exercised; the `ui_*` tools target a running bridged desktop application. See the [agent guide](https://github.com/storytold/filmcraft/blob/v0.20.1/docs/agents.md) and [control protocol](https://github.com/storytold/filmcraft/blob/main/docs/control-protocol.md).

Every row except sequence inspection is a `tools/call` whose payload is `{"name":"command_run","arguments":{"id":"ENGINE_ID","params":{...}}}`. Use the returned imported item IDs in steps 3–4; do not hard-code IDs.

| Step | ID / tool | Verified arguments |
| --- | --- | --- |
| 1. Create portrait sequence | `file.newSequence` | `{"name":"Portrait check","width":360,"height":640,"fps":24,"video":1,"audio":1}` |
| 2. Import synthetic red and blue clips with audio | `file.import` | `{"paths":["/work/inputs/red.mp4","/work/inputs/blue.mp4"]}`; require two returned items and no errors. |
| 3. Place first clip | `timeline.place` | `{"item":FIRST_ID,"track":"V1","seconds":0,"duration":{"seconds":0.5},"audio":true}` |
| 4. Place second clip | `timeline.place` | `{"item":SECOND_ID,"track":"V1","seconds":0.5,"duration":{"seconds":0.75},"audio":true}` |
| 5. Inspect total time | `sequence_inspect` | Direct tool with `{}`; expect `durationFrames:30`. |
| 6. Render new output | `file.exportMedia` | `{"path":"/work/outputs/portrait-proof.mp4","format":"h264","range":"entire","audio":true,"wait":true}` |

Example fixture generation (inputs are one second each; then mount read-only):

```sh
mkdir -p inputs outputs
ffmpeg -n -v error -f lavfi -i color=c=red:s=360x640:r=24:d=1 -f lavfi -i sine=f=440:r=48000:d=1 -shortest -c:v libx264 -pix_fmt yuv420p -c:a aac inputs/red.mp4
ffmpeg -n -v error -f lavfi -i color=c=blue:s=360x640:r=24:d=1 -f lavfi -i sine=f=660:r=48000:d=1 -shortest -c:v libx264 -pix_fmt yuv420p -c:a aac inputs/blue.mp4
```

Verify `offlineMedia:[]`, no warnings, an export result of 30 frames and a nonempty new file. On the tested proof, independent decoding found H.264 360×640 at 24 fps, 30 video frames, an AAC stream, and approximately 1.25 s duration (container duration 1.258 s). Frame samples at 0.25 and 0.75 s decoded predominantly red and blue, respectively; full decode reported no errors. Never read the API's render elapsed time as media duration.

```sh
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,nb_frames:format=duration -of json outputs/portrait-proof.mp4
ffmpeg -v error -i outputs/portrait-proof.mp4 -f null -
```

A second isolated synthetic run used the same engine and operations with a 1080×1920 30 fps sequence, two 30 fps sources, and 0.50 s + 0.70 s trimmed placements. It returned 36 video frames with no warnings or offline media. Independent checks verified H.264 yuv420p, stereo AAC at 48 kHz, 1.216 s container duration, and a full error-free decode. This proves the delivery profile with synthetic footage, not HDR, third-party codecs, complex titles, or a real campaign.

## When a result does not qualify

- If an asset, library, font, codec or runtime feature is absent, show the missing component; try an upstream build or different trusted runner only after rechecking configuration. Do not declare unsupported features broken across platforms on one Linux result.
- If FilmCraft hits an import/codec issue, transcode **a staged copy** to a simple, tested mezzanine (e.g., H.264/AAC with known dimensions, frame rate and timestamps), then repeat inspection. A long job may require using returned `jobs.list`/cancel controls if documented by the pinned runner; verify output after completion and before any retry. For a repeatable basic cut when FilmCraft is unavailable and the user requested a render, use a scoped FFmpeg workflow and report that fallback by name; it is not FilmCraft validation.
- For optional titles or unusual effects an independent rendered preview is required. Use a verified transparent or rendered interchange artifact where appropriate; headless smoke tests don't establish transition, VFX, alpha, color/HDR, GUI, GPU, hardware-encoding or real project parity. See [FilmCraft architecture](https://github.com/storytold/filmcraft/blob/main/docs/architecture.md) for OS-dependent codecs and acceleration. Prefer portable H.264/AAC for the synthetic delivery check.
- Keep the editable project and sources separate from shareable exports. Do not promise project round-trip in untested formats. If a production render is needed, test a short sample with the real assets (only with authorization), inspect video and audio together, and keep distribution as a separate decision.

Additional official documentation: [EffectCraft MCP and confinement](https://github.com/storytold/effectcraft/blob/main/docs/mcp.md), [SoundCraft CLI](https://github.com/storytold/soundcraft/blob/main/docs/cli.md), [PhotoCraft source/releases](https://github.com/storytold/photocraft/releases), [FilmCraft 0.20.1 release](https://github.com/storytold/filmcraft/releases/tag/v0.20.1), [Craft Anything scope and status](https://github.com/storytold/craft-anything).
