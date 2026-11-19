#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build the presenter and share copies of a single-file HTML deck.

Usage:
  build.py SRC.html [--out-dir dist] [--name NAME]

Reads SRC.html and writes two files:
  OUT/NAME.html         presenter build: speaker notes kept (press N in the deck)
  OUT/NAME-share.html   share build: the NOTES block and the notes panel are REMOVED from the file,
                        not hidden, so the file can be sent without the talk track

Placeholders in SRC (paths are relative to SRC's folder):
  {{notes_enabled}}   -> true (presenter) or false (share)
  {{img:PATH}}        -> base64 data URI (png, jpg, svg, webp...)
  {{font:PATH}}       -> base64 data URI for a .woff2 font
  {{svg:PATH}}        -> inline <svg> markup (XML header and <title> dropped)
  {{raw:PATH}}        -> file contents verbatim

The source must carry the markers  /* NOTES:BEGIN */ ... /* NOTES:END */  and an
<aside class="notes" id="notes"> panel; the build refuses otherwise, so a share copy can never
silently keep the notes. Python 3.9+, standard library only.
"""
import argparse
import base64
import mimetypes
import pathlib
import re
import sys

PLACEHOLDER = re.compile(r"\{\{(font|img|svg|raw):([A-Za-z0-9_./@ -]+)\}\}")
NOTES_BLOCK = re.compile(r"/\* NOTES:BEGIN \*/.*?/\* NOTES:END \*/", re.S)
NOTES_ASIDE = re.compile(r'<aside class="notes" id="notes".*?</aside>', re.S)
SHARE_MUST_NOT_CONTAIN = ("NOTES:BEGIN", 'class="confirm"', 'id="notes-body"')


def data_uri(path: pathlib.Path, mime: str) -> str:
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def inline_svg(path: pathlib.Path) -> str:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"<\?xml[^>]*\?>", "", text)
    text = re.sub(r"<title>.*?</title>", "", text, flags=re.S)
    return text.strip()


def expand(src: str, base: pathlib.Path) -> str:
    def repl(m: re.Match) -> str:
        kind, rel = m.group(1), m.group(2)
        path = base / rel
        if kind == "font":
            return data_uri(path, "font/woff2")
        if kind == "img":
            return data_uri(path, mimetypes.guess_type(str(path))[0] or "application/octet-stream")
        if kind == "svg":
            return inline_svg(path)
        return path.read_text(encoding="utf-8")
    return PLACEHOLDER.sub(repl, src)


def build(src: str, base: pathlib.Path, share: bool) -> str:
    out = src
    if share:
        out = NOTES_BLOCK.sub("const NOTES = [];", out)
        out = NOTES_ASIDE.sub("", out)
    out = out.replace("{{notes_enabled}}", "false" if share else "true")
    return expand(out, base)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src")
    ap.add_argument("--out-dir", default="dist")
    ap.add_argument("--name", help="output base name (default: the source file name without .html)")
    a = ap.parse_args()

    src_path = pathlib.Path(a.src).resolve()
    base = src_path.parent
    src = src_path.read_text(encoding="utf-8")
    missing = [m.group(0) for m in PLACEHOLDER.finditer(src) if not (base / m.group(2)).exists()]
    if missing:
        print("missing assets:", *missing, sep="\n  ", file=sys.stderr)
        return 1
    if not NOTES_BLOCK.search(src) or not NOTES_ASIDE.search(src):
        print("notes markers not found; refusing to build a share copy that might still carry notes", file=sys.stderr)
        return 1

    out_dir = pathlib.Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    name = a.name or src_path.stem
    for share, suffix in ((False, ""), (True, "-share")):
        out = build(src, base, share)
        if share:
            for needle in SHARE_MUST_NOT_CONTAIN:
                if needle in out:
                    print(f"share build still contains {needle!r}; refusing to write it", file=sys.stderr)
                    return 1
        path = out_dir / f"{name}{suffix}.html"
        path.write_text(out, encoding="utf-8")
        print(path, f"{path.stat().st_size:,} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
