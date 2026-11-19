#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Write double-click launchers for a built demo: macOS .command and Windows .bat, one per mode.

Usage:
  make_launchers.py DEMO.html [--playlist all] [--browser chrome|edge]

Writes next to DEMO.html:
  Start-Staffed   app window (no address bar), ?mode=staffed
  Start-Presenter app window, ?mode=presenter
  Start-Kiosk     full-screen kiosk, ?mode=kiosk     (visitors drive; idle return; no staff controls on screen)
  Start-Wall      full-screen kiosk, ?mode=wall&playlist=KEY  (hands-free loop from the first item)
Each launcher opens a separate browser profile in the temp folder, so kiosk flags work even when the browser is
already open, and finds the demo next to itself, so the folder can live anywhere. Leave a kiosk window with Alt+F4
(Windows) or Cmd+Q (macOS). The launchers were written for Chrome and Edge and were not run on a real Mac or
Windows machine by this build; try each one once before the event. Python 3.9+, standard library only.
"""
import argparse
import pathlib
import stat

MODES = [("Staffed", "--app={u}", "mode=staffed"), ("Presenter", "--app={u}", "mode=presenter"),
         ("Kiosk", "--kiosk {u}", "mode=kiosk"), ("Wall", "--kiosk {u}", "mode=wall&playlist={pl}")]
MAC_APP = {"chrome": "Google Chrome", "edge": "Microsoft Edge"}
WIN_EXE = {"chrome": "chrome", "edge": "msedge"}

MAC = """#!/bin/bash
# Opens {name} in {app} ({label}). Double-click to start.
DIR="$(cd "$(dirname "$0")" && pwd)"
URL="file://$DIR/{name}?{query}"
open -na "{app}" --args {flag} --user-data-dir="${{TMPDIR:-/tmp}}/demo-{slug}" --no-first-run --disable-session-crashed-bubble
"""
WIN = """@echo off
rem Opens {name} in {exe} ({label}). Double-click to start.
set "F=%~dp0{name}"
set "F=%F:\\=/%"
start "" {exe} {flag} --user-data-dir="%TEMP%\\demo-{slug}" --no-first-run --disable-session-crashed-bubble
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("demo")
    ap.add_argument("--playlist", default="all")
    ap.add_argument("--browser", choices=sorted(MAC_APP), default="chrome")
    a = ap.parse_args()
    demo = pathlib.Path(a.demo)
    if not demo.is_file():
        raise SystemExit(f"{demo} not found")
    for label, flag, query in MODES:
        q = query.format(pl=a.playlist)
        slug = label.lower()
        mac = demo.parent / f"Start-{label}.command"
        mac.write_bytes(MAC.format(name=demo.name, app=MAC_APP[a.browser], label=label, query=q,
                                   flag=flag.format(u='"$URL"'), slug=slug).encode("utf-8"))
        mac.chmod(mac.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        win = demo.parent / f"Start-{label}.bat"
        win.write_bytes(WIN.format(name=demo.name, exe=WIN_EXE[a.browser], label=label, query=q,
                                   flag=flag.format(u=f'"file:///%F%?{q}"'), slug=slug).replace("\n", "\r\n").encode("utf-8"))
        print(f"wrote {mac.name} and {win.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
