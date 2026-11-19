#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Rebuild the worked example and run every check. Needs Python 3.9+ only. Run from anywhere.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
pc="$here/../../skills/presentation-coach"
hp="$here/../../skills/humanize-pass"
out="$here/built"
mkdir -p "$out"

echo "== notes, talk track, deck"
python3 "$pc/scripts/notes_from_spec.py" "$here/talk-track-spec.json" "$here/deck.src.html" | tail -1
python3 "$pc/scripts/build_talk_track.py" "$here/talk-track-spec.json" "$out/acme-ledger-talk-track.html" \
  --md "$out/acme-ledger-talk-track.md" | tail -2
python3 "$pc/scripts/build.py" "$here/deck.src.html" --out-dir "$out" --name acme-ledger

echo "== number sources"
python3 "$pc/scripts/untraced_numbers.py" --spec "$here/talk-track-spec.json" --deck "$out/acme-ledger-share.html" \
  --figures "$here/FIGURES.md" --allow "$here/allow.txt" > "$out/numbers.md"
tail -1 "$out/numbers.md"

echo "== sensitivity"
python3 "$pc/scripts/sensitivity_check.py" --config "$here/sensitivity.json" \
  "$out/acme-ledger-share.html" "$out/acme-ledger-talk-track.html" "$out/acme-ledger-talk-track.md" \
  "$here/QA.md" "$here/REHEARSAL.md"

echo "== offline"
python3 "$pc/scripts/offline_check.py" "$out/acme-ledger.html" "$out/acme-ledger-share.html" "$out/acme-ledger-talk-track.html"

echo "== prose tells"
python3 "$hp/scripts/ai_tells.py" "$out/acme-ledger-talk-track.md" "$here/QA.md" "$here/REHEARSAL.md" "$here/README.md" | tail -1
