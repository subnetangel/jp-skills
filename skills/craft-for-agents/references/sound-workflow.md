# SoundCraft workflow: cues, Foley, loops and clean voice

Use SoundCraft for arranging, editing, mixing and rendering locally. It is a DAW, not a text-to-music or voice-cloning service. Start in a disposable project. Deliver dry/clean sources, stems and a mix separately when useful; keep the editable session plus its managed audio directory together.

## Pick the sound and plan the handoff

| Need | Build | Check and deliver |
| --- | --- | --- |
| **Original cue** | Define picture hit, duration and mood. Use a short synth motif for identity, layered transient/body/tail for impact, or filtered noise for whoosh. Leave head/tail room; place markers or write exact cue times. | Listen against picture, solo cue layers, verify onset/timecode and headroom. Export the mix plus clean variations (short/long, dry/wet) when requested. |
| **Foley** | Record a sound you can use, or generate it from oscillators/noise. Align the first meaningful transient to the action; use a small attack/release to suppress accidental clicks without softening the hit. Build several variations, not just repetitions. | Listen at realistic level with the picture. Isolate distracting noise, left/right balance and unintended reverse/pops. Deliver named one-shots, aligned stem and cue sheet as needed. |
| **Music loop** | Set BPM, meter, bar count and exact loop range first. Begin with an original rhythmic/melodic pattern; use instrument tracks, MIDI or owned audio. For release/reverb crossing the seam, render into the next repetition and carry decay into the loop head, or keep tails on a separate one-shot. | Bounce from exact sample/bar boundaries. Concatenate at least three decoded copies, inspect and listen across both joins, and check that timing and tails do not pump or skip. Deliver PCM loop with BPM/bars and exact sample length, plus optional tail and stems. |
| **Vocal cleanup** | Get authorization to use the recording; duplicate the track/project and preserve dry audio. Trim obvious defects with short fades; use clip gain before processing. Try a gentle high-pass for rumble, narrow correction for measured hum/resonance, modest compression/dynamics for consistency, and de-ess only when needed. Use gentle expansion rather than hard gating if words or breaths disappear. | Level-match A/B against the dry copy. Audit consonants, sibilance, breaths and quiet words, check hum/noise before/after, and listen for pumping or clipped phrase ends. Deliver clean stem and a mix, not an invented 'restored' recording. |

Rights are separate from technical ability. Check consent/release for voices, permission and license scope for samples, loops, recordings and generated assets, and any required attribution. Do not assume a demo is cleared for redistribution, mimic an identifiable performer, or send audio to an external tool without approval.

## Pinned local MCP setup

[SoundCraft 0.20.1 release](https://github.com/storytold/soundcraft/releases/tag/v0.20.1), Linux x86-64 tar archive SHA-256 `caefcf85c4f1138717d592d31ce5be07f2fca616ec36d63fac6760cdefbe28a9` (matched upstream checksum manifest; not independent signer verification). Use the extracted `bin/soundcraft-cli`; see the [CLI reference](https://github.com/storytold/soundcraft/blob/main/docs/cli.md) and [MCP guide](https://github.com/storytold/soundcraft/blob/main/docs/mcp.md). Check local `--version` and `mcp --help` before starting. Use an MCP client that supports local stdio:

```sh
soundcraft-cli mcp --automation-read-root /job/inputs --automation-write-root /job/outputs
```

Use actual absolute, scoped directories; no desktop `--connect`, account, plugins beyond built-ins, or listeners. Keep project inputs read-only at the OS layer where possible. App-native roots confine the supported automation file paths, not networking or the OS as a whole; use a network-denied job sandbox for sensitive sources. Launch with capped time/storage and close stdin/reap the process when done. For an MCP client: `initialize`, validate negotiated protocol/version, notify `notifications/initialized`, then `tools/list`. Treat `isError` and JSON-RPC errors as failures; some results carry JSON in the text content. Inspect available schemas and one-shot `soundcraft-cli describe COMMAND` when a build differs.

## Verified fresh build via MCP

This starts with a **blank** project, not the bundled demo. The synth music is original MIDI built in SoundCraft. Two monochannel 48 kHz PCM inputs are generated outside it with standard math: a 0.20 s transient (a short attack and exponential decay on one-pole filtered, seeded noise), and a 2 s synthetic dynamics test signal (pulsed 220 Hz tone, low-level noise and 40 Hz rumble). The latter is deliberately **not a real vocal**, and EQ insertion is not proof of rumble removal.

Direct MCP calls are `tools/call` with `{"name":"TOOL","arguments":{...}}`. Engine calls use the direct `execute` tool: `{"name":"execute","arguments":{"command":"ENGINE_ID","params":{...}}}`. Use the clip ID returned from step 4. Integer time positions here are samples except parameters explicitly named `*_ticks`.

| Step | Tool or engine ID | Tested parameters |
| --- | --- | --- |
| 1 | `new_session` | `{"template":"blank","name":"Synthetic sound check","sample_rate":48000}` |
| 2 | `event.tempo` | `{"bpm":120,"at":0}` |
| 3 | `track.new` | `{"kind":"instrument","name":"Synth","format":"stereo","instrument":"subtractive_synth"}` |
| 4 | `midi.new_clip` | `{"track":"Synth","start":0,"end":{"seconds":2}}` |
| 5 | `midi.note_add` ×4 | `{"clip":CLIP_ID,"pitch":48,"start_ticks":0,"length_ticks":360,"velocity":75}`; pitches 48/55/60/55, ticks 0/960/1920/2880. |
| 6 | `track.new`, then `import_audio` | Mono audio tracks named Foley and Signal. `{"path":"/job/inputs/foley.wav","track":"Foley","at":{"seconds":0.25}}`; import test signal on Signal at 0 s. |
| 7 | `mix.volume`, `mix.insert` | `{"track":"Foley","db":-6}` and same for Signal; `{"track":"Signal","slot":0,"plugin":"eq_7band"}`. EQ at defaults in this proof. |
| 8 | `save_session` | `{"path":"/job/outputs/synthetic.scraft"}`; keep companion `Audio Files/`. |
| 9 | `file.bounce_stems` | Precreate clean directory; `{"dir":"/job/outputs/stems","format":"wav","bit_depth":24,"start":0,"end":96000,"dither":false}`. |
| 10 | `bounce_mix` | `{"path":"/job/outputs/mix.wav","format":"wav","bit_depth":"24","start":0,"end":96000}`. This MCP tool wants a **string** bit depth. |
| 11 | `mix.solo`, then `bounce_mix` | `{"tracks":["Synth"],"value":true,"exclusive":true}`; bounce same range to new `music-loop.wav`. Done after project save so the saved full mix is not soloed. |

For cleanup beyond those tested steps, inspect the pin with `describe edit.fades_create`, `describe clip.gain`, `describe mix.insert`, and `describe mix.insert_param`; use the exact plugin parameter IDs from that build. The pin lists built-ins including `eq_7band`, `compressor`, `expander_gate`, and `de_esser`; listing them does not prove all processing paths or a suitable preset. Do not guess at parameter IDs, apply a restoration preset blindly, or claim dedicated denoising if unavailable.

## Verify before delivery

1. **Formats and alignment:** On every bounce run a full decode, not just a header inspection. Check sample rate, bit depth, channels, sample count and expected onset. Export all stems from the same zero/range, not from each region's first note. Solo each stem; verify buses/sidechains and gain staging. A nonlinear master bus means isolated stems may not sum to the mastered mix; document routing, or export an unmastered reference and stems at common gain. Native mono tracks in this proof bounced as stereo stems.
2. **Seam:** Compare each channel's last and first decoded sample and inspect the waveform/slope around the join. A small jump is only an indicator; assemble repeated copies and listen for clicks, phase/ambience changes, silence, repeated transients and timing drift. Test the target player/codec. Sample-accurate WAV is preferable to relying on lossy encoder padding being removed. No one threshold guarantees an inaudible seam.
3. **Level:** Measure integrated LUFS and oversampled true peak independently, e.g. FFmpeg `ebur128`; sample peak is not true peak. Judge short effects by peaks/context as well, because integrated loudness and gating are less meaningful for tiny clips. Set targets for the actual delivery spec; don't normalize every stem or loop blindly. Check final encoded asset again and retain headroom unless the spec dictates otherwise. See [ITU-R BS.1770](https://www.itu.int/rec/R-REC-BS.1770/en) and the [FFmpeg filter reference](https://ffmpeg.org/ffmpeg-filters.html#ebur128-1).
4. **Reference commands** (local verification only; unique staged outputs):
   ```sh
   ffprobe -v error -show_entries stream=codec_name,sample_rate,channels,bits_per_sample,duration_ts -of json outputs/music-loop.wav
   ffmpeg -v error -i outputs/music-loop.wav -f null -
   ffmpeg -hide_banner -i outputs/mix.wav -af ebur128=peak=true -f null -
   ffmpeg -n -v error -i outputs/music-loop.wav -filter_complex '[0:a]asplit=3[a][b][c];[a][b][c]concat=n=3:v=0:a=1[out]' -map '[out]' -c:a pcm_s24le outputs/music-loop-repeat-qa.wav
   ```

**Fresh-proof result:** SoundCraft created and saved one blank-origin project, copied two input WAVs to managed audio, rendered three stems, one full mix and a synth-only loop. All five exported WAVs independently decoded non-silent at stereo PCM 24-bit/48 kHz, exactly 96,000 frames. Full mix: SoundCraft reported −32.35 LUFS and −21.92 dBTP; independent FFmpeg measured −32.4 LUFS and −21.9 dBTP. Synth loop: four note attacks showed up in decoded RMS windows; last-to-first max channel jump was `0.000041` of full scale. This is numeric seam evidence, not an audition, creative quality verdict, vocal-cleanup outcome or mastering target.

## Limits and fallback

- Headless verifies engine calls and file export, not live recording, audio devices, GUI-only actions, third-party plugins, real speech repair, or destination interoperability. Preview the exact production asset before claiming its quality.
- If the pinned MCP cannot perform a supported operation, try equivalent **pinned CLI** only within the same scope. If native routing or processing is missing, a scoped FFmpeg/audio-library pass can generate test fixtures, trim/fade, filter, measure or stitch; keep an untouched original and label which tool actually produced each file. If the sound cannot be cleaned without damage, report the residual or request a new take instead of overprocessing.
- No external generator, third-party asset, upload or publication is required for this workflow. For an actual deliverable, preserve editable source, export receipt (tool version, render range, channels/rate/format, peak/LUFS, rights note), and vetted outputs as distinct artifacts.
