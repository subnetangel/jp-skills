@echo off
rem Opens acme-ledger-demo.html in chrome (Staffed). Double-click to start.
set "F=%~dp0acme-ledger-demo.html"
set "F=%F:\=/%"
start "" chrome --app="file:///%F%?mode=staffed" --user-data-dir="%TEMP%\demo-staffed" --no-first-run --disable-session-crashed-bubble
