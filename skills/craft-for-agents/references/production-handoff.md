# Multi-format production and handoff

Use this when a job has several media types, needs editable handoff, or asks for Craft work outside photo, sound, design or video. [The app matrix](craft-tools.md) lists tested versions and scope. A successful smoke test proves only the operation shown.

## Build the deliverable, not a tool parade

Decide on source of truth and inspect a representative slice before batching. Keep the editable master in its native format, and number derived exports. Write outputs to a new job folder, never back into the sources. Freeze design tokens or measurements only after seeing the proposed deliverable at its real size. If the task is a draft, deliver only a draft; don't create a cloud project or publish by default.

| Handoff | Safer default | Verify before importing downstream |
|---|---|---|
| Photo into layout/video | Full-resolution finished still, with web/delivery crop exported separately | Orientation, color profile, target crop, edited vs original at matched size |
| Logo or type into layout/motion | Editable SVG or native file plus rendered PNG reference | Intended fonts or outlines in a delivery copy, no unintended external assets, contrast, bounds and transparency |
| Graphic into motion | Transparent PNG/image sequence for interchange or a rendered overlay when compositing alpha is unproven | Alpha and edge appearance against light and dark backgrounds, dimensions, cadence and color |
| Sound into video | Aligned WAV stems plus full mix; for a normal video job start at 48 kHz or match the actual spec | Same start time and sample rate, sync and polarity, not clipped, no seam click; listen to the encoded video as well |
| Model or materials into a 3D scene | Units/axis note plus geometry and separately named PBR maps | Dimensions, scale, winding/normals, project color-space conventions and correct map slots |
| Document to review or print | Editable source plus rendered PDF where useful | Pagination, legibility, link and text checks, actual receiver/viewer, paper/bleed/profile when specified |
| Spreadsheet to analysis | Editable workbook; CSV only for agreed sheet/range | Recalculated formulas, date/time zone, delimiter/encoding, hidden rows/sheets and leading zeros |

Where a receiver requests a specialized format, do a small import/reopen test there instead of claiming compatibility from file extension or an export receipt.

## Documents, decks, PDFs and workbooks

- **WordCraft:** use a document source for flowing text; verify headings, page breaks, names, numbers and styles; provide DOCX plus PDF only as needed. The pinned smoke built text, saved and reopened DOCX with the same text, then exported a PDF. It did not prove full Word round-trip, advanced layout or accessibility.
- **DeckCraft:** separate editable slides from speaker notes and previews. Build the story around one point per slide; validate each slide's rendered text size, overflow, art and timing before handing it off. The pinned smoke saved and reopened a native deck, exported PPTX and produced a PNG. Open the real presentation in the receiving app when possible; animations, fonts and media are not established by the smoke.
- **PdfCraft:** inspect page order, boxes, fields, attachments, layers and encryption before touching a source. The pinned test used `doc_open({path})`, `doc_set_info({doc,key:"Title",value:"Synthetic proof"})`, `page_rotate({doc,degrees:90,pages:[1]})`, `doc_save({doc,path})` and `doc_export_text({doc,path})`. Use the returned document ID, a separate save path and the discovered schema. Independently check the rotated page, visible layout and extractable text. A colored overlay is not redaction: if asked to redact, use a proven removal workflow and confirm the information is absent from visible layers, text, metadata and attachments. Treat active PDF content as untrusted.
- **GridCraft:** set units and source links, record input cells and expected formula results, check negatives/blanks and dates, then reopen XLSX and compare a small sample. The pinned smoke set `A1` to 21 and `B1` to `=A1*2`, confirmed 42 after reopen, and read `21,42` from CSV. CSV drops formulas, formatting and other sheets; treat unexpected formula-like values as data rather than executing them.

## CAD, textures and procedural materials

Use **CADCraft** for precise geometry, **TextureCraft** for painting/baking against a mesh, and **MaterialCraft** for procedural surface maps. Do not substitute raster art for dimensioned drawings. Document the units, basis/origin, orientation, resolution and channel conventions of the receiving tool; evaluate with a small geometric or checker fixture before a large export. A synthetic CAD smoke exported one closed rectangle to parsed SVG; it did not prove tolerance, STEP interchange or fabricability. A MaterialCraft smoke exported and decoded six small maps (base color, normal, roughness, metallic, occlusion and height), not engine equivalence. Pack channels only when the receiving engine specifies its order; preview on a neutral test object under at least two lighting angles. Color maps and data maps usually need different color-space handling. Do not assume tangent-space normal convention, shader color space or scale from an image name.

For fixtures or print/production geometry, keep design assumptions visible and hand off the editable source and matching proof; don't imply industry compliance or engineering approval from file QA.

## Fictional example: workshop launch kit

Grade one approved hero photo in PhotoCraft, make a matching title and reusable badge in DesignCraft/VectorCraft, create an original cue in SoundCraft, and use FilmCraft only if the brief asks for video. Review the photo before it is cropped into templates; check the badge at the smallest real size; preserve a clean cue and WAV mix. Deliver `workshop-hero-v02.jpg`, `workshop-badge-v02.svg`, `workshop-cue-v02.wav`, and a native project package only where the requested output requires it. No live distribution is implied.

Primary references: [official Crafting Apps](https://getartcraft.com/apps), [PdfCraft](https://github.com/storytold/pdfcraft), [WordCraft](https://github.com/storytold/wordcraft), [DeckCraft](https://github.com/storytold/deckcraft), [GridCraft](https://github.com/storytold/gridcraft), [CADCraft](https://github.com/storytold/cadcraft), [TextureCraft](https://github.com/storytold/texturecraft), [MaterialCraft](https://github.com/storytold/materialcraft).
