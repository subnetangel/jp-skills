#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Write VERSION.txt into a package folder: version, build time, source commit, the demo file's SHA-256, and the
SHA-256 and size of every file in the folder. Staff compare the hash on their laptop with this file.

    version_manifest.py PACKAGE_DIR --version v1.4 --demo Demo-v1.4.html [--repo .] [--notes notes.txt] [--title "..."]

--notes is appended as written (what each loop shows, the runs and the product version each was recorded on, how
to open the file). Refuses a package folder or demo name that release_guard.py says is released.
"""
import argparse
import datetime
import hashlib
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from release_guard import refuse_released  # noqa: E402


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("package")
    ap.add_argument("--version", required=True)
    ap.add_argument("--demo", required=True, help="the demo HTML's file name inside the package")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--notes")
    ap.add_argument("--title", default="Booth demo")
    a = ap.parse_args()
    refuse_released(os.path.join(a.package, "VERSION.txt"))
    commit = subprocess.run(["git", "-C", a.repo, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    rows = []
    for d, _, fs in sorted(os.walk(a.package)):
        for f in sorted(fs):
            p = os.path.join(d, f)
            if f == "VERSION.txt":
                continue
            rows.append(f"  {sha(p)}  {os.path.getsize(p):>11}  {os.path.relpath(p, a.package)}")
    demo = os.path.join(a.package, a.demo)
    if not os.path.exists(demo):
        sys.exit(f"{demo} not found")
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    text = "\n".join([a.title, f"Version: {a.version}", f"Build date: {now}", f"Source commit: {commit or 'unknown'}", "",
                      f"Demo HTML: {a.demo}", f"SHA-256: {sha(demo)}", "", "All files (SHA-256, bytes):", *rows, ""])
    if a.notes:
        text += "\n" + open(a.notes).read().rstrip() + "\n"
    open(os.path.join(a.package, "VERSION.txt"), "w").write(text)
    print(f"VERSION.txt: {len(rows)} files, demo {sha(demo)[:8]}, commit {commit}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
