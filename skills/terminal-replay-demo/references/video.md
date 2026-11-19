# Loops and the fallback video

Render the replay terminal itself to video, so a frame of the video is the replay's frame at the same step and a fix
reaches the video on the next render.

## With Remotion (optional)

Follow the `terminal-replay` skill, section "Video, optional": export the timeline with `build_replay.py --timeline`,
install the official Remotion agent skills with `npx skills add remotion-dev/skills`, and have the agent follow
`remotion-create`, `remotion-captions` and `remotion-render`. Remotion's licence page
([remotion.dev/license](https://www.remotion.dev/license)) says: "Remotion is free to use for individuals and
companies up to three people. Obtaining a Company License is required only for entities ineligible for the Free
License." Check your own eligibility first; the official `remotion-license` skill covers the terms.

## Without Remotion

Open the replay page in a headless browser, play it with `?speed=1`, and record the page; then encode H.264 with
any ffmpeg build that lists `libx264` (`ffmpeg -hide_banner -encoders | grep 264`). If H.264 is a problem for you,
VP9 WebM plays in Chrome and Edge; check the venue's video player first, since a screen with no laptop may need MP4.

## Booth loops

One looping MP4 per playlist, for screens with no laptop:

1. Render each item once to `out/items/<item>-<theme>.mp4`.
2. **Render all items first, then build the concat list.** In the worked example, rendering inside the list loop
   left only the last item in the output.
3. Join with the concat demuxer and stream copy, which works only when every item has the same codec, size and frame
   rate: `ffmpeg -f concat -safe 0 -i list.txt -c copy -movflags +faststart out/loops/loop-all-dark.mp4`.
4. `-movflags +faststart` so a player starts at once.
5. Record in `VERSION.txt` which commit the loops were rendered from.

## Fallback video

A full run of the main scenario as one MP4 in the staff package, so a presenter whose laptop fails can still show
the story. Check it like the page: stills at the key moments (`ffmpeg -ss <t> -i video.mp4 -frames:v 1 still.png`),
compared with the page at the same step; the "recreated" label present; the length in `VERSION.txt`; one full play
on the target player.
