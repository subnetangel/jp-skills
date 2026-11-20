#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check a local reel MP4 against the skill's house delivery profile."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from fractions import Fraction


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="approved export directory")
    parser.add_argument("--allow-silent", action="store_true", help="permit no audio stream")
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    try:
        root = args.root.resolve(strict=True)
        path = args.file.resolve(strict=True)
        if not root.is_dir() or not path.is_file() or path.suffix.lower() != ".mp4" or not path.is_relative_to(root):
            raise ValueError("expected a local .mp4 inside the export directory")
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-protocol_whitelist", "file",
             "-f", "mov", "-show_format", "-show_streams", "-of", "json", str(path)],
            capture_output=True, text=True, check=True, timeout=30,
        )
        data = json.loads(result.stdout)
        videos = [s for s in data["streams"] if s.get("codec_type") == "video"
                  and not s.get("disposition", {}).get("attached_pic")]
        audios = [s for s in data["streams"] if s.get("codec_type") == "audio"]
        v, a = next(iter(videos), {}), next(iter(audios), {})
        size = [v.get("width"), v.get("height")]
        fps = float(Fraction(v.get("avg_frame_rate") or "0")) if v.get("avg_frame_rate") != "0/0" else 0.0
        sar = v.get("sample_aspect_ratio")
        rotation = any(float(s.get("rotation", 0)) % 360 for s in v.get("side_data_list", []))
        seconds = float(data.get("format", {}).get("duration", 0))
        checks = {
            "video_streams": len(videos) == 1,
            "dimensions": size == [1080, 1920] and not rotation and sar in ("1:1", None, "N/A"),
            "fps": abs(fps - 30) <= 0.1,
            "video_codec": v.get("codec_name") == "h264" and v.get("pix_fmt") == "yuv420p",
            "audio_codec": (not a and args.allow_silent) or (
                len(audios) == 1 and a.get("codec_name") == "aac"
                and a.get("sample_rate") == "48000" and a.get("channels") == 2),
            "duration": seconds > 0,
        }
        failed = [key for key, passed in checks.items() if not passed]
        print(json.dumps({"profile": "house-reel-1080p30", "dimensions": size,
                          "fps": fps, "seconds": seconds, "failed": failed}, indent=2))
        return int(bool(failed))
    except (OSError, ValueError, KeyError, ZeroDivisionError,
            subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        print(f"Could not audit the reel: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
