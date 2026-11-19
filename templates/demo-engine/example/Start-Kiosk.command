#!/bin/bash
# Opens acme-ledger-demo.html in Google Chrome (Kiosk). Double-click to start.
DIR="$(cd "$(dirname "$0")" && pwd)"
URL="file://$DIR/acme-ledger-demo.html?mode=kiosk"
open -na "Google Chrome" --args --kiosk "$URL" --user-data-dir="${TMPDIR:-/tmp}/demo-kiosk" --no-first-run --disable-session-crashed-bubble
