#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Record ONE real CLI session on a pty, typing one prompt like a person would, in `script -T timing -B io` format.

    record_pty.py --out DIR --name turn1 --prompt-file p.md [--idle-regex RE] [--quiet 90] [--max 5400]
                  [--boot RE=KEYS ...] [--quit-keys '/quit\\r'] [--cols 140 --rows 45] -- <cli command ...>

Writes DIR/<name>.io (the byte stream, with script's header and footer lines) and DIR/<name>.timing (util-linux
advanced format: H header records, O output and I input records), so `scriptreplay -T X.timing -B X.io` replays it.

How a turn runs:
  1. Start the command on a pty of --cols x --rows, in THIS process's session and process group (no setsid, no
     `script`): some agent hosts reap processes that start a new session (a capture lost turns to this).
  2. Answer one-time boot screens: each --boot 'REGEX=KEYS' sends KEYS once when REGEX appears (escapes: \\r \\n \\e).
  3. When the CLI is ready (it printed --idle-regex, or the screen has been quiet for --boot-quiet s), type the prompt
     one character at a time, then Enter.
  4. Wait until the CLI is idle again and the screen has been quiet for --quiet s (or --max s in total), then send
     --quit-keys (default: none, close the pty) and record the exit.
It never types anything else. An approval or any other human decision is never typed by this driver.
Refuses to overwrite an existing recording.
"""
import argparse
import fcntl
import os
import re
import select
import struct
import subprocess
import sys
import termios
import time
from datetime import datetime, timezone


def keys(s: str) -> bytes:
    return s.encode().decode("unicode_escape").replace("\\e", "\x1b").encode("latin-1")


class Recorder:
    def __init__(self, io_path, timing_path, cols, rows):
        self.io, self.tm = open(io_path, "wb"), open(timing_path, "w")
        self.t0 = self.prev = time.time()
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S+00:00")
        for k, v in (("START_TIME", stamp), ("TERM", os.environ.get("TERM", "xterm-256color")), ("TTY", "pty"),
                     ("COLUMNS", cols), ("LINES", rows), ("SHELL", os.environ.get("SHELL", "/bin/sh"))):
            self.tm.write(f"H 0.000000 {k} {v}\n")
        self.io.write(f'Script started on {stamp} [TTY="pty" COLUMNS="{cols}" LINES="{rows}"]\n'.encode())

    def rec(self, kind, data):
        now = time.time()
        self.tm.write(f"{kind} {now - self.prev:.6f} {len(data)}\n")
        self.prev = now
        self.io.write(data)

    def close(self, code):
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S+00:00")
        self.tm.write(f"H 0.000000 DURATION {time.time() - self.t0:.6f}\nH 0.000000 EXIT_CODE {code}\n")
        self.io.write(f'\nScript done on {stamp} [COMMAND_EXIT_CODE="{code}"]\n'.encode())
        self.io.close(); self.tm.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--prompt-file", required=True)
    ap.add_argument("--idle-regex", help="bytes regex the CLI prints when it waits for input (e.g. a prompt glyph)")
    ap.add_argument("--quiet", type=float, default=90, help="seconds of quiet after the answer before quitting")
    ap.add_argument("--boot-quiet", type=float, default=5, help="seconds of quiet that count as ready, without --idle-regex")
    ap.add_argument("--max", type=float, default=5400, help="hard cap on the whole turn, seconds")
    ap.add_argument("--boot", action="append", default=[], help="REGEX=KEYS, answered once")
    ap.add_argument("--quit-keys", default="")
    ap.add_argument("--type-delay", type=float, default=0.01)
    ap.add_argument("--cols", type=int, default=140)
    ap.add_argument("--rows", type=int, default=45)
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    a = ap.parse_args()
    cmd = a.cmd[1:] if a.cmd[:1] == ["--"] else a.cmd
    if not cmd:
        ap.error("no command after --")
    os.makedirs(a.out, exist_ok=True)
    io_path, tm_path = (os.path.join(a.out, f"{a.name}.{x}") for x in ("io", "timing"))
    if os.path.exists(io_path) or os.path.exists(tm_path):
        sys.exit(f"refusing: {io_path} exists (a capture is never overwritten)")
    prompt = " ".join(open(a.prompt_file).read().split())
    idle = re.compile(a.idle_regex.encode()) if a.idle_regex else None
    boots = [(re.compile(b.split("=", 1)[0].encode()), keys(b.split("=", 1)[1])) for b in a.boot]
    rec = Recorder(io_path, tm_path, a.cols, a.rows)

    fd, tty = os.openpty()
    fcntl.ioctl(tty, termios.TIOCSWINSZ, struct.pack("HHHH", a.rows, a.cols, 0, 0))
    proc = subprocess.Popen(cmd, stdin=tty, stdout=tty, stderr=tty, close_fds=True,
                            env=dict(os.environ, TERM=os.environ.get("TERM", "xterm-256color"),
                                     COLUMNS=str(a.cols), LINES=str(a.rows)))
    os.close(tty)

    def send(b: bytes):
        os.write(fd, b)
        rec.rec("I", b)

    start = last = time.time()
    buf, phase, answered = b"", "boot", set()
    while True:
        r, _, _ = select.select([fd], [], [], 0.5)
        now = time.time()
        if r:
            try:
                data = os.read(fd, 65536)
            except OSError:
                break
            if not data:
                break
            rec.rec("O", data)
            last, buf = now, (buf + data)[-20000:]
        elif proc.poll() is not None:
            break
        if phase == "boot":
            hit = next((i for i, (p, _) in enumerate(boots) if i not in answered and p.search(buf)), None)
            if hit is not None:
                time.sleep(0.5); send(boots[hit][1]); answered.add(hit); buf = b""
            elif (idle.search(buf) if idle else True) and now - last > a.boot_quiet:
                for ch in prompt:
                    send(ch.encode()); time.sleep(a.type_delay)
                time.sleep(0.5); send(b"\r")
                phase, buf, last = "prompted", b"", time.time()
            elif now - start > 180:
                print(f"{a.name}: the CLI never became ready", file=sys.stderr)
                proc.terminate(); break
        elif phase == "prompted":
            ready = idle.search(buf[-4000:]) if idle else True
            if (ready and now - last > a.quiet) or now - start > a.max:
                if a.quit_keys:
                    send(keys(a.quit_keys))
                    phase = "quitting"
                else:
                    break
        elif now - last > 60:
            break
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(10)
        except subprocess.TimeoutExpired:
            proc.kill()
    code = proc.wait()
    rec.close(code)
    print(f"{a.name}: exit={code} elapsed={int(time.time() - start)}s phase={phase} capped={time.time() - start > a.max}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
