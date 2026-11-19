#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build one golden-cut segment from a REDACTED cast (never from raw), and log every edit.

    cut_segment.py --src redacted/run1/turn1 --dst cut/scenario/01-turn1 --label "Recorded in a test account · synthetic names"
                   [--names names.json] [--max-gap 2.0] [--changes cut/scenario/CHANGES.md]

The only edits, each written as one line to --changes:
  1. Label: a banner line with --label is added at the start of the cast (an O record of its own).
  2. Synthetic names: names.json is a list of [old, new] pairs; every pair MUST be the same length, so the .timing byte
     counts stay valid. A pair of different lengths is refused.
  3. Timing: any pause longer than --max-gap seconds is shortened to --max-gap. Bytes are untouched.
Results are never edited: a refusal, a stop, an error or a blocked step stays exactly as recorded.
"""
import argparse
import json
from pathlib import Path


def read_cast(stem: Path):
    header, _, body = stem.with_suffix(".io").read_bytes().partition(b"\n")
    lines = stem.with_suffix(".timing").read_text().splitlines()
    events = [[p[0], float(p[1]), int(p[2])] for p in (l.split(" ", 2) for l in lines) if p[0] in ("O", "I")]
    return header, body, events, [l for l in lines if l.startswith("H ")]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True, type=Path, help="redacted cast stem (without .io/.timing)")
    ap.add_argument("--dst", required=True, type=Path)
    ap.add_argument("--label", required=True)
    ap.add_argument("--names", type=Path)
    ap.add_argument("--max-gap", type=float, default=2.0)
    ap.add_argument("--changes", type=Path)
    a = ap.parse_args()
    if "raw" in a.src.parts:
        raise SystemExit("refusing: cut segments are built from the redacted copy, never from raw")
    header, body, events, head = read_cast(a.src)
    n0 = len(body)
    text = body.decode("latin-1")
    pairs = json.loads(a.names.read_text()) if a.names else []
    for old, new in pairs:
        if len(old.encode()) != len(new.encode()):
            raise SystemExit(f"name pair not the same length: {old!r} -> {new!r}")
        text = text.replace(old.encode().decode("latin-1"), new.encode().decode("latin-1"))
    body = text.encode("latin-1")
    assert len(body) == n0
    raw_total = sum(d for _, d, _ in events)
    events = [[k, min(d, a.max_gap), n] for k, d, n in events]
    banner = f"\x1b[0m\x1b[7m {a.label} \x1b[0m\r\n".encode()
    body, events = banner + body, [["O", 0.0, len(banner)]] + events
    a.dst.parent.mkdir(parents=True, exist_ok=True)
    a.dst.with_suffix(".io").write_bytes(header + b"\n" + body)
    a.dst.with_suffix(".timing").write_text("\n".join(head + [f"{k} {d:.6f} {n}" for k, d, n in events]) + "\n")
    new_total = sum(d for _, d, _ in events)
    line = (f"- `{a.dst.name}` <- redacted `{a.src}`: banner \"{a.label}\"; {len(pairs)} same-length renames; "
            f"pauses over {a.max_gap:g}s cut, replay {raw_total / 60:.1f} -> {new_total / 60:.1f} min.")
    if a.changes:
        with a.changes.open("a") as f:
            f.write(line + "\n")
    print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
