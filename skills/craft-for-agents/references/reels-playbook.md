# Reels: plan, cut, test

## 1. Make the idea easy to share

Pick the audience and one result: **discovery** (qualified reach/shares), **consideration** (saves/profile visits), or **action** (qualified clicks, inquiries or purchases). Write the viewer promise in one sentence and name the visual or audible evidence. Read [Reels evidence](reels-evidence.md) for platform guidance and case-study limitations. The following are hypotheses, not volatile ranking rules or guaranteed winners.

| Format to test | Example opening | Proof and payoff | Best first metric |
|---|---|---|---|
| Reveal / transformation | Open on the real after shot, then flash the before | Same angle where possible; show one or two changes and the result | Shares / reach |
| Useful checklist or quick fix | Show the mistake and say who it costs time | Demonstrate each step and the resulting change; number the steps | Saves / reach |
| POV / relatable micro-story | Start inside a familiar situation, not with a logo | Setup → tension → recognizable turn → resolution | Shares / reach |
| Tour / sensory escape | Start with the best real view and ambient sound | Give three true details, then a closing view worth sending | Shares / reach; next test profile visits |
| Test / surprising comparison | Put two outcomes side by side | Explain one variable, show the test, then give the actual result | Watch ratio and shares / reach |
| Product or service demo | Show the job being done in frame one | Problem → use → result → one appropriate next step | Qualified actions / reach |

Develop two different **openers**, not two fully different edits. One might show the outcome; the other might show the friction or ask a specific question. Don't withhold the whole payoff just to manufacture a loop. Verify claims; don't stage fake before/after footage as fact. If an educational idea needs 30 seconds, don't cut the proof to match an alleged perfect length.

## 2. Cut for the phone

1. **Select first.** Log source ranges with named subjects, proof shots, faces, movement, clean ambient/audio, and rights. Outlines and transcripts help find selects, not replace judgment. Build in a 9:16 project and manually reframe faces, hands, and on-screen text; don't stretch landscape.
2. **Make the first beat work muted.** Use one visible subject and one promise. Try a 0–2 s opening, context by about 5 s, proof through the middle, and a decisive payoff. A 12–25 s cut is a useful starting experiment for a narrow idea; a demonstration can use longer beats. These are editorial defaults, not requirements. Start mid-action, cut dead air, use cutaways over joins and let proof breathe. Use a pattern change only when it adds information. A loop is optional.
3. **Mix and caption.** Cut dialogue for clarity first. Preserve intelligible speech and useful location sound; duck licensed music beneath it, fix abrupt changes, and listen at low phone volume as well as in headphones. Correct names, numbers and subtitles manually. Use high contrast, short phrase breaks, and room for visible subjects. Check captions with sound off; avoid rapid flashing.
4. **Check actual placement.** Preview captions, branding, faces, and the call to action with the destination's live overlay and profile/feed cover crop. Keep essential text clear of the top/bottom and right side controls; don't treat a generic pixel safe zone as a platform guarantee. Use a cover with a meaningful focal point, a readable title and a ready caption. Do not put critical text solely in a transient title or cover.
5. **Choose tools per task.** FilmCraft for sequence/trim/export; PhotoCraft or LightCraft for still treatment; DesignCraft for cover/brand assets; EffectCraft for a motivated title or composited element; SoundCraft to prepare or mix authorized audio. Only use native caption or mixing features once discovered and proven. Use editable or separate intermediates where possible; hand off the source project, a clean master if needed, a captioned delivery file or SRT, cover and a short QC note. See [toolchain and fallback](craft-tools.md).

### Suggested delivery profile and QA

For a new vertical master, use **1080×1920**, square pixels, **30 fps** by default, H.264 MP4 with yuv420p, and stereo AAC at 48 kHz when audio is present. This is a conservative house target, not a claim that every platform or Craft version requires it. Keep a cadence-preserving editorial master if needed, avoid unnecessary re-encodes, and check the specific platform/placement/organic-vs-paid requirements at delivery. Check the final transfer, not only the edit preview.

Optional local, read-only metadata check (Python 3.9+ and ffprobe on PATH):

```sh
python3 scripts/reel_qa.py --root ./exports ./exports/reel-v01.mp4
ffmpeg -v error -nostdin -xerror -protocol_whitelist file -i ./exports/reel-v01.mp4 -f null -
```

The checker reports house-profile mismatches (exit 1) or a file/tool error (exit 2); intentional silent files can use `--allow-silent`. The decoder command checks media errors, not captions, consent, black frames, audio intelligibility, or composition. Compare decoded video duration and cut timing to the approved edit plan (normally within one output frame for frame-aligned cuts; container duration may include audio padding). Play the rendered first frame, title, cuts and last frame in portrait; listen to the final mix. If fallback encoding altered cadence/color, compare it against the source master.

### Worked paper cut: prove a transformation

For a fictional workshop showing a desk reset, version A opens on the completed desk; version B opens on the clutter and the question “What would you move first?” At 1.5 s both switch to the same angle for the before frame. At 3 s show the first demonstrable action; at 6 s show the second; at 9 s show a clean matched-angle comparison with natural sound; at 13 s leave the payoff legible and give one useful next step. Caption any speech. If the reference footage is not cleared, rebuild the *structure* with owned shots, not its clips, melody, dialogue, exact graphical treatment or identifiable people. Keep both exports, the edit decision list, and the rights log. These timestamps are a fictional edit sketch, not a measured winning reel.

## 3. Learn from results without confusing them for causation

- **Before posting:** record the objective, one main metric, one changing variable, the draft/cut version, audience, distribution type, planned windows and decision rule. Keep topic, body cut, cover, length, rights, CTA, budget, account and release conditions as similar as practical; if the opener changes duration, log the difference.
- **First pass:** capture a 24-hour read and a 72-hour read (or fixed equivalent); use a 7-day snapshot for conversion lag where useful. If Instagram Trial is available and authorized, use manual share and comparable trials; Trial is distribution to non-followers first, not a randomized split. A weak first few hours or tiny reach is not a rejection rule. Do not mix follower tests, post types or paid boosts in the same baseline.
- **Metrics:** use platform-reported early retention where available; otherwise mark it missing. Report average watch seconds and `average watch seconds / reel seconds` as a normalized watch ratio, not completion (rewatches can make it exceed 100%). Use shares/reach, saves/reach, and attributed qualified actions/reach; keep numerators and reach beside rates. Distinguish views (may include replays) from unique reach. Compare across the same age and objective; use tracked links or a campaign code for actions when appropriate.
- **Decision:** start with the median and spread of the last 10–20 comparable account posts if enough exist. For an outlier, report lift against that baseline and absolute reach rather than calling any fixed number viral. Look for a direction that repeats on at least three paired ideas before adopting a hook as a house pattern. Declare a low-volume or contradictory read inconclusive. Paid creative splits can estimate effects more cleanly if randomized and held equal, but keep their CPA/ROAS and learnings separate.
- **Diagnose the next edit:** low early retention → first-frame claim/visual mismatch; good early retention but a dip before proof → remove setup; strong watches and low shares/saves → give the viewer a stronger reason to pass it on or return; good reach but low qualified actions → check audience fit, CTA and landing flow before recutting. Treat these as hypotheses; inspect the actual cut and analytics.

For TikTok or Shorts: export a clean watermark-free master, adjust opener rhythm/caption and placement per destination, recheck music rights, and use each platform's own metric definitions. Don't compare raw view counts across platforms.
