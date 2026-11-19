#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build the demo into ONE self-contained HTML file.

Usage:
  build.py SRC.html OUT.html [--staff-code-file PATH | --ask-staff-code] [--launchers]

Placeholders in SRC (paths relative to this template folder):
  {{css:PATH}} {{js:PATH}} {{raw:PATH}}   file contents, verbatim
  {{json:PATH}}                         a JSON file, parsed and re-serialized ("</" escaped so it cannot end a script)
  {{img:PATH}} {{font:PATH}} {{video:PATH}}   base64 data URIs (png, jpg, svg, webp, gif, woff2, woff, ttf, mp4, webm)
  {{staff_code_sha256}}                 SHA-256 of the staff code. Only the hash is written, never the code.

The staff code comes from the first line of --staff-code-file (keep that file out of git), or from a hidden prompt
with --ask-staff-code. With neither, the build uses the placeholder code 0000 and says so: fine for trying the
template, wrong for a booth. The staff code is a convenience gate, not security.

The build refuses to write when a placeholder is left unfilled or a referenced file is missing. It prints the size
and SHA-256 of the output; put both in your VERSION file. --launchers also writes double-click launchers next to the
output (see launchers/make_launchers.py). Python 3.9+, standard library only.
"""
import argparse
import base64
import getpass
import hashlib
import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PH = re.compile(r"\{\{(css|js|raw|json|img|font|video):([A-Za-z0-9_./@ -]+)\}\}")
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".svg": "image/svg+xml", ".webp": "image/webp",
        ".gif": "image/gif", ".woff2": "font/woff2", ".woff": "font/woff", ".ttf": "font/ttf", ".mp4": "video/mp4",
        ".webm": "video/webm"}
PLACEHOLDER_CODE = "0000"


def fill(m):
    kind, rel = m.group(1), m.group(2).strip()
    p = (HERE / rel).resolve()
    if HERE not in p.parents and p != HERE:
        sys.exit(f"REFUSED: {rel} is outside the template folder")
    if not p.is_file():
        sys.exit(f"REFUSED: {rel} not found")
    if kind in ("css", "js", "raw"):
        return p.read_text(encoding="utf-8")
    if kind == "json":
        return json.dumps(json.loads(p.read_text(encoding="utf-8")), ensure_ascii=False).replace("</", "<\\/")
    mime = MIME.get(p.suffix.lower())
    if not mime:
        sys.exit(f"REFUSED: no MIME type for {rel}")
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode('ascii')}"


def staff_code(a):
    if a.staff_code_file:
        code = pathlib.Path(a.staff_code_file).read_text(encoding="utf-8").splitlines()[0].strip()
    elif a.ask_staff_code:
        code = getpass.getpass("Staff code (not echoed): ").strip()
    else:
        print(f"NOTE: placeholder staff code {PLACEHOLDER_CODE} in use; set your own before a booth "
              "(--staff-code-file or --ask-staff-code)")
        code = PLACEHOLDER_CODE
    if not code:
        sys.exit("REFUSED: empty staff code")
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src")
    ap.add_argument("out")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--staff-code-file")
    g.add_argument("--ask-staff-code", action="store_true")
    ap.add_argument("--launchers", action="store_true", help="also write Chrome kiosk and app launchers")
    a = ap.parse_args()
    src = pathlib.Path(a.src).read_text(encoding="utf-8")
    page = PH.sub(fill, src)          # one pass: inlined files are not scanned for placeholders again
    page = page.replace("{{staff_code_sha256}}", staff_code(a))
    left = re.findall(r"\{\{[a-z_]+(?::[^}]*)?\}\}", page)
    if left:
        sys.exit(f"REFUSED: unfilled placeholders: {sorted(set(left))[:5]}")
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    data = page.encode("utf-8")
    out.write_bytes(data)
    print(f"wrote {out} ({len(data):,} bytes) sha256 {hashlib.sha256(data).hexdigest()}")
    if a.launchers:
        subprocess.run([sys.executable, str(HERE / "launchers" / "make_launchers.py"), str(out)], check=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
