#!/bin/bash
# Opens acme-ledger-demo.html in Google Chrome (Staffed). Double-click to start.
DIR="$(cd "$(dirname "$0")" && pwd)"
URL="file://$DIR/acme-ledger-demo.html?mode=staffed"
open -na "Google Chrome" --args --app="$URL" --user-data-dir="${TMPDIR:-/tmp}/demo-staffed" --no-first-run --disable-session-crashed-bubble
