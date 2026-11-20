# Craft workflow: graphics, layouts, UI, and motion

Pick the app from the **deliverable**, not the input extension. Ask what someone will open, print, or edit next. Keep the editable source and a separate proof/export. Use an approved copy of the input, and never overwrite a master, share an invite, or publish as a side effect of editing.

| Outcome | Start here | Deliver and verify |
| --- | --- | --- |
| Retouched photo, composited graphic, or transparent artwork | [PhotoCraft](photo-workflow.md). Keep the original; use layers or masks so a reviewer can undo targeted changes. | Editable native project when requested, plus an sRGB JPEG for photography or a PNG when transparency matters. Reopen the export; compare framing, dimensions, color, shadow detail, and edge halos against the original. |
| Logo, icon, diagram, or editable illustration | [VectorCraft](https://getartcraft.com/apps/vectorcraft). Build from paths and named groups; keep live editable text in the master. | Native source plus SVG for handoff, or PDF/PNG for the destination. Reopen the SVG in the recipient's editor; test viewBox, fonts, clipping, fills, and editability. Provide an outlined export only if needed, never instead of the editable master. |
| Flyer, booklet, or other print layout | [DesignCraft](https://getartcraft.com/apps/designcraft) for page layout, styles and bleed; [PdfCraft](https://github.com/storytold/pdfcraft) for PDF inspection or requested page operations. Obtain trim, bleed, color profile and PDF standard from the print vendor before export. | Editable layout, linked assets, and print PDF. Check trim/bleed boxes, page order, font embedding, selectable text, and color requirements. For digital distribution, make a separate screen PDF; don't claim PDF/X, PDF/A or accessibility compliance without validating that exact requirement. |
| UI flow, design system, or clickable prototype | [FigCraft](https://getartcraft.com/apps/figcraft). Define frames, components, variants and responsive constraints, then wire a default path and at least one alternate state. | Native design, optional prototype, and handoff notes. Test narrow and wide frames, focus/interaction states and the requested navigation. A generated code sample is not a shipped app. |
| 2D animated logo, explainer, or interactive-style motion | [AniCraft](https://getartcraft.com/apps/anicraft). Start with staged vector shapes; confirm frame rate, easing, loop seam and whether the destination needs alpha. | Editable timeline plus a format the destination actually plays. Inspect first, middle, and final frames, then play the entire loop; confirm duration, frame rate and transparency rather than inferring them from the extension. |
| Title composite, keyed overlay, or tracked visual effect | [EffectCraft](https://getartcraft.com/apps/effectcraft) for the shot or composite; [FilmCraft](https://getartcraft.com/apps/filmcraft) for the assembled edit. Check that the installed builds support a common interchange before committing. | Editable effect source, a rendered intermediate, and the final cut when in scope. Test compositing edges over light and dark backgrounds, color-space matching, effect handles, sync and export playback. |
| Finished video with multiple shots | [FilmCraft](craft-tools.md#filmcraft-verified-edit-inspect-and-export). Build the sequence from explicitly staged clips and keep them with the timeline. | Editable timeline and correctly sized video export. Independently decode the output; check runtime, frame order, frame rate, codec, missing assets and audio levels. |

## Run a small proof before the full job

1. **Define the acceptance check.** Record delivery size, aspect ratio, editability, color/audio needs, and destination format. If there is no reviewer or destination spec, choose a reasonable default and label it.
2. **Discover the installed build.** Verify the publisher, release digest, OS and architecture. Check the actual CLI or MCP command catalog. A working CLI does not establish that the MCP or GUI works.
3. **Choose the narrowest execution route.** Prefer a scoped local/headless process for repeatable exports. Use a GUI for interaction that genuinely requires it. Isolate an app with no native folder limits at the operating-system level before exposing tool access. Give a disposable test only the input and output it needs.
4. **Proof the hardest operation.** Export one representative page, symbol, frame, or clip, then reopen it independently and check what the recipient will see. Expand only after the proof passes.
5. **Deliver source + release.** Name both clearly, attach dependencies if needed, and provide a terse verification note: what opened, what passed, and what was not tested. A smoke test does not establish broad compatibility or production readiness.

## Two verified native exports

Use the confined local MCP procedure and discover the installed schemas in [Craft tools](craft-tools.md). The examples below were exercised on pinned Linux x86-64 builds; the commands illustrate a minimal synthetic proof, not full support across all formats.

**DesignCraft 0.20.1: a graphic with an editable text object.** Start a scoped MCP process with `designcraft-cli mcp --automation-read-root <input-dir> --automation-write-root <output-dir>`. Call:

1. `new_document({"width":200,"height":120,"title":"Synthetic smoke"})`
2. `execute({"command":"frame.create","params":{"rect":[15,15,190,90],"content":"text","text":"Synthetic smoke"}})`
3. `export_png({"path":"<absolute-output-dir>/proof.png","scale":1})`

Confirm a decoded 200×120 RGBA image with visible nonuniform content, then check alignment and typography in a viewer. Native re-editability and print standards still need their own proof. See [DesignCraft MCP docs](https://github.com/storytold/designcraft/blob/main/docs/mcp.md).

**EffectCraft 0.24.1: build and render a simple title.** In a scoped, authorized session, wrap each operation in the discovered `command_run` tool using the command as `id` and the supplied object as `params`:

| Command | Arguments |
| --- | --- |
| `comp.new` | `{"name":"Synthetic title","width":320,"height":180,"frameRate":12,"duration":1}` |
| `layer.newSolid` | `{"color":"#136f63"}` |
| `layer.newText` | `{"text":"SYNTHETIC TITLE","size":32,"fill":"#ffffff"}` |
| `renderQueue.add` | `{"comp":"Synthetic title","format":"h264","output":"<absolute-output-dir>/title.mp4","start":0,"end":1,"audio":"off"}` |
| `renderQueue.render` | `{"wait":true}` |

Use a fresh output name. The proof decoded all 12 frames of the 320×180 H.264 export, displayed the title in a PNG preview, and rejected an out-of-root export. H.264 in this test was a flattened, silent preview, not an alpha interchange format. Discover and independently test an alpha-capable export before using it downstream. See [EffectCraft MCP docs](https://github.com/storytold/effectcraft/blob/main/docs/mcp.md).
