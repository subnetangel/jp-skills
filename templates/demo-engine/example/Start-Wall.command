#!/bin/bash
# Opens acme-ledger-demo.html in Google Chrome (Wall). Double-click to start.
DIR="$(cd "$(dirname "$0")" && pwd)"
URL="file://$DIR/acme-ledger-demo.html?mode=wall&playlist=all"
open -na "Google Chrome" --args --kiosk "$URL" --user-data-dir="${TMPDIR:-/tmp}/demo-wall" --no-first-run --disable-session-crashed-bubble
