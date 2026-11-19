#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Never rebuild under a released name. RELEASED.txt lists every released file as '<sha256>  <file name>', where the
file name ends in -v<version>.html. Every script that writes an output asks this guard first.

    release_guard.py check PATH ...          exit 1 if any path carries a released version tag
    release_guard.py record FILE             append FILE's sha256 and name to RELEASED.txt (after the upload)
    release_guard.py dirty REPO [PATHS ...]  exit 1 if the source paths have uncommitted changes
    release_guard.py --self-test

A version tag like v1.4 marks every file and folder of that release (Demo-v1.4.html, Demo-v1.4-cards.pdf,
Demo-v1.4/ package folder). A '-dev' build of a released version is allowed: its names say '-dev' and never ship.
RELEASED.txt is found next to this script, or at $RELEASED_FILE.
In Python: from release_guard import refuse_released; refuse_released(out_path)
"""
import hashlib
import os
import re
import subprocess
import sys

RELEASED = os.environ.get("RELEASED_FILE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "RELEASED.txt"))
TAG = re.compile(r"-(v\d+(?:\.\d+)+)\.html$")


def released_versions(path=None):
    path = path or RELEASED
    if not os.path.exists(path):
        return []
    names = [l.split()[-1] for l in open(path) if l.strip()]
    return sorted({m.group(1) for n in names for m in [TAG.search(n)] if m})


def released_tag(path, released=None):
    parts = os.path.abspath(path).split(os.sep)
    for v in released_versions(released):
        pat = re.compile(r"-" + re.escape(v) + r"(?!\d|\.\d|-dev)")
        if any(pat.search(p) for p in parts):
            return v
    return None


def refuse_released(path, released=None):
    v = released_tag(path, released)
    if v:
        sys.exit(f"refusing to write {path}: {v} is released ({released or RELEASED}). Give the build a new version.")


def dirty(repo, paths):
    out = subprocess.run(["git", "-C", repo, "status", "--porcelain", "--", *paths], capture_output=True, text=True, check=True)
    return out.stdout.strip()


def record(file, released=None):
    released = released or RELEASED
    if not TAG.search(os.path.basename(file)):
        sys.exit(f"{file}: the released file name must end in -v<version>.html")
    sha = hashlib.sha256(open(file, "rb").read()).hexdigest()
    with open(released, "a") as f:
        f.write(f"{sha}  {os.path.basename(file)}\n")
    print(f"recorded {sha[:8]}  {os.path.basename(file)} in {released}")


def self_test():
    import tempfile
    d = tempfile.mkdtemp()
    rel = os.path.join(d, "RELEASED.txt")
    open(rel, "w").write("0" * 64 + "  Demo-2026-v1.4.html\n" + "1" * 64 + "  Demo-2026-v1.10.2.html\n")
    cases = [("dist/Demo-2026-v1.4.html", "v1.4"), ("dist/Demo-2026-v1.4-share.html", "v1.4"),
             ("dist/package/Demo-v1.4/VERSION.txt", "v1.4"), ("dist/Demo-2026-v1.4-dev.html", None),
             ("dist/Demo-2026-v1.40.html", None), ("dist/Demo-2026-v1.4.1.html", None),
             ("dist/Demo-2026-v1.10.2-cards.pdf", "v1.10.2"), ("dist/Demo-2026-v99.0.html", None)]
    bad = [(p, want, got) for p, want in cases for got in [released_tag(p, rel)] if got != want]
    for b in bad:
        print("FAIL", b)
    print(f"release guard: {len(cases) - len(bad)} of {len(cases)} cases pass")
    return 1 if bad else 0


def main(argv):
    if argv[:1] == ["--self-test"]:
        return self_test()
    if len(argv) >= 2 and argv[0] == "check":
        hits = [(p, released_tag(p)) for p in argv[1:]]
        for p, v in hits:
            print(f"{'REFUSE' if v else 'ok'} {p}" + (f" ({v} is released)" if v else ""))
        return 1 if any(v for _, v in hits) else 0
    if len(argv) == 2 and argv[0] == "record":
        record(argv[1]); return 0
    if len(argv) >= 2 and argv[0] == "dirty":
        d = dirty(argv[1], argv[2:])
        if d:
            print("uncommitted source changes; commit first, or build with a -dev name:\n" + d)
        return 1 if d else 0
    sys.exit(__doc__)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
