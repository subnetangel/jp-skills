# Shared screen modes for demo stations

One set of names, keys and link options for every station, so rotating staff can run any demo. The demo-engine
template in this repository implements all of it; a demo built another way should map its own controls to these
names and list the gaps.

## 1. Modes

| Mode | Who drives | What is on screen | Idle |
|---|---|---|---|
| `staffed` (default) | staff and visitors | every control | back to the first screen after the idle time |
| `presenter` | one presenter, keys or a clicker | minimal chrome | never |
| `kiosk` | visitors, unattended | no staff controls, no slide picker, no theme switch | back to the first screen |
| `wall` | nobody | a hands-free loop and a pause control | a paused loop resumes |

## 2. Staff entry

A key chord (the template uses Ctrl+Alt+S), a gear button outside kiosk and wall modes, or `?admin` in the link,
then a staff code. The code is a convenience gate against visitors switching modes by accident, never security:
the file holds only a hash of it, and nothing goes behind it that a visitor may not see.

## 3. Link options

| Option | Effect |
|---|---|
| `?mode=staffed|presenter|kiosk|wall` | start in that mode |
| `?playlist=KEY` | the list of screens the wall loop plays |
| `?speed=N` | playback speed for recreated runs and the loop |
| `?theme=light|dark` | start in that theme |
| `?lock` | hide staff controls in staffed or presenter mode |
| `?idle=SECONDS` | idle time before the return to the first screen; `0` turns it off |
| `?admin` | open the staff entry on load |
| `?reset` | forget an unlocked staff session and the saved theme |
| `#N` | open screen N |

## 4. Keys

→ Space PgDn next · ← PgUp back · 1-9 jump · Home End · G slide picker · L theme · F full screen · P pause the loop
or the recreated run · Esc close a panel. A demo's own key must not reuse one of these for something else.

## 5. Idle and reset

After the idle time with no input, close every panel, go to the first screen and restart any recreated run, so the
next visitor never sees the last visitor's state. Presenter mode never resets on its own.

## 6. The loop

The wall loop always starts at the first item of its playlist and plays the list in order. Each screen stays for
its dwell time; a screen with a recreated run stays until the run finishes. Keys do nothing in the loop except the
pause key and the staff chord. A visible pause control stops it.
