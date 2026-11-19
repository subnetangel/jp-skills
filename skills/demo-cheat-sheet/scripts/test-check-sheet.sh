#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Smoke test for check-sheet.py: a bad sheet must fail on each rule, a good one must pass.
set -u
here=$(cd "$(dirname "$0")" && pwd)
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
usd='$'; fake_id="1234567""89012"; ok_id="5555""5555""5555"   # built at run time so this file holds no literal figure or ID
sections='## What it is
## What the product delivers
## 30-second pitch
## How to drive it
## Three key points
## Likely questions
## What not to claim
## Offline and kiosk notes'
printf "%s\nSaves ${usd}100 a month. Account ${fake_id}. Codename Blue. Separate parallel lanes.\n" "$sections" > "$tmp/bad.md"
printf "%s\nAccount ${ok_id} is a documentation placeholder. Separate parallel lanes.\n" "$sections" > "$tmp/good.md"
printf '## What it is\n' > "$tmp/short.md"
printf 'Blue\nPAR\n' > "$tmp/deny.txt"
fail=0
out=$(python3 "$here/check-sheet.py" "$tmp/bad.md" --deny-file "$tmp/deny.txt")
for want in 'dollar figure' '12-digit number' 'denied term: Blue'; do
  grep -q "$want" <<<"$out" || { echo "MISSING: $want"; fail=1; }
done
grep -q 'denied term: PAR' <<<"$out" && { echo "FALSE HIT: PAR inside a word"; fail=1; }
python3 "$here/check-sheet.py" "$tmp/good.md" --deny-file "$tmp/deny.txt" --allow-id "$ok_id" >/dev/null || { echo "good sheet failed"; fail=1; }
python3 "$here/check-sheet.py" "$tmp/short.md" | grep -q 'missing section: Likely questions' || { echo "missing-section rule"; fail=1; }
[ $fail = 0 ] && echo "test-check-sheet: PASS" || { echo "test-check-sheet: FAIL"; exit 1; }
