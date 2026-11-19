@echo off
rem Opens acme-ledger-demo.html in chrome (Presenter). Double-click to start.
set "F=%~dp0acme-ledger-demo.html"
set "F=%F:\=/%"
start "" chrome --app="file:///%F%?mode=presenter" --user-data-dir="%TEMP%\demo-presenter" --no-first-run --disable-session-crashed-bubble
