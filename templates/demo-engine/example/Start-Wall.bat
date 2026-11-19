@echo off
rem Opens acme-ledger-demo.html in chrome (Wall). Double-click to start.
set "F=%~dp0acme-ledger-demo.html"
set "F=%F:\=/%"
start "" chrome --kiosk "file:///%F%?mode=wall&playlist=all" --user-data-dir="%TEMP%\demo-wall" --no-first-run --disable-session-crashed-bubble
