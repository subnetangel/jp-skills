#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Make a redacted COPY of one raw capture folder. The raw folder is never modified.

    redact_cast.py RULES.json RAW_DIR REDACTED_DIR

Terminal recordings (*.io) are redacted LENGTH-PRESERVING, so the paired *.timing byte counts stay valid and
`scriptreplay -T X.timing -B X.io` still replays the copy. Other text files (JSON, HTML, Markdown, logs, prompts) get
the same rules without the length constraint. Images and other binaries are NOT copied: they need a person's
redaction pass. File names are redacted too.

RULES.json (keep it next to the raw captures, outside git; it names the real values):
  {
    "example_id": "<twelve zeros>",               # every 12-digit number becomes this (never inside a hex digest)
    "real_ids": ["<your real 12-digit identifier>"],  # also caught when a TUI splits them across escapes or a wrap
    "rules": [["regex", "replacement"], ...],     # your names: codename, aliases, fixture prefix, hostnames, paths
    "split": [["regex", "replacement"], ...],     # tokens a TUI may print in pieces (checked on the escape-free view)
    "skip_dirs": ["home", ".agent", ".config"]    # agent home, installed skills, client configs: never copied
  }
Built-in rules run first: cloud access-key ids of the AKIA/ASIA shape, long secret-like blobs, every 12-digit number
not inside a hex run, IPv4 addresses, UUIDs. In a .io file every replacement is padded or cut to the length it
replaces. (The older keys "example_account" and "real_accounts" still work.)
"""
import json
import os
import re
import sys

ESC = re.compile(r"\x1b\[[0-9;?<>=]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b[()][A-Za-z0-9]")
TEXT_EXT = {".json", ".jsonl", ".md", ".html", ".txt", ".log", ".yaml", ".yml", ".csv", ".prompt", ".timing",
            ".started", ".finished", ".svg"}


def same_len(repl: str, orig: str, pad: str = "x") -> str:
    return (repl + pad * len(orig))[:len(orig)]


def build_rules(cfg):
    acct = cfg.get("example_id", cfg.get("example_account", "0" * 12))
    real = cfg.get("real_ids", cfg.get("real_accounts", []))
    rules = [
        (re.compile(r"\b(AKIA|ASIA)[A-Z0-9]{16}\b"), lambda m: same_len("AKIAEXAMPLE", m.group(0), "X")),
        (re.compile(r"(?<![A-Za-z0-9+/])(?=[A-Za-z0-9+/]*[A-Z])(?=[A-Za-z0-9+/]*[a-z])[A-Za-z0-9+/]{60,}={0,2}"),
         lambda m: "x" * len(m.group(0))),
        # a 12-digit run that is not part of a hex digest or a decimal (a sha256 must survive unchanged)
        (re.compile(r"(?<![\dA-Fa-f.])\d{12}(?![\dA-Fa-f.])"), lambda m: acct),
        (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), lambda m: re.sub(r"\d", "0", m.group(0))),
        (re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"),
         lambda m: "eeeeeeee-0000-0000-0000-eeeeeeeeeeee"),
    ]
    for pat, repl in cfg.get("rules", []):
        rules.append((re.compile(pat), lambda m, r=repl: r))   # redact_io pads or cuts it to the matched length
    hexguard = r"(?<![\dA-Fa-f]){}(?![\dA-Fa-f])"   # never inside a digest: hashes must survive unchanged
    split = [(re.compile(hexguard.format(re.escape(a))), acct) for a in real]
    # a line-wrapped identifier: any 6-digit piece of it standing alone at a wrap point
    split += [(re.compile(hexguard.format(a[i:i + 6])), acct[i:i + 6]) for a in real for i in (0, 3, 6)]
    split += [(re.compile(p), r) for p, r in cfg.get("split", [])]
    return rules, split


def redact_text(text, rules):
    for pat, fn in rules:
        text = pat.sub(fn, text)
    return text


def redact_io(data: bytes, rules, split) -> bytes:
    """Decode as latin-1 (1 byte = 1 char) so every replacement keeps the byte count of what it replaced."""
    text = data.decode("latin-1")
    out = text
    for pat, fn in rules:
        out = pat.sub(lambda m: same_len(fn(m), m.group(0), " "), out)
    if len(out) != len(text):
        raise SystemExit("redaction changed the stream length; refusing to write a broken replay")
    # second pass on the escape-free view: tokens printed in pieces with escape codes in between
    keep, pos = [], 0
    for m in ESC.finditer(out):
        keep.extend(range(pos, m.start())); pos = m.end()
    keep.extend(range(pos, len(out)))
    view = "".join(out[i] for i in keep)
    chars = list(out)
    for pat, repl in split:
        for m in pat.finditer(view):
            for k, j in enumerate(range(m.start(), m.end())):
                chars[keep[j]] = (repl + " " * len(m.group(0)))[k]
    return "".join(chars).encode("latin-1")


def main() -> int:
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    cfg = json.load(open(sys.argv[1]))
    src, dst = (os.path.abspath(p) for p in sys.argv[2:4])
    if (dst + os.sep).startswith(src + os.sep):
        sys.exit("destination is inside the raw folder")
    rules, split = build_rules(cfg)
    skip = set(cfg.get("skip_dirs", ["home", ".agent", ".config", "__pycache__"]))
    n = 0
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in skip]
        rel = os.path.relpath(root, src)
        out_dir = os.path.join(dst, redact_text(rel, rules) if rel != "." else "")
        os.makedirs(out_dir, exist_ok=True)
        for f in files:
            p, ext = os.path.join(root, f), os.path.splitext(f)[1]
            q = os.path.join(out_dir, redact_text(f, rules))
            if ext == ".io":
                open(q, "wb").write(redact_io(open(p, "rb").read(), rules, split))
            elif ext in TEXT_EXT:
                open(q, "w").write(redact_text(open(p, errors="replace").read(), rules))
            else:
                continue          # binaries and screenshots: a person redacts those, never this script
            n += 1
    print(f"redacted {n} files -> {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
