@echo off
rem Opens acme-ledger-demo.html in chrome (Kiosk). Double-click to start.
set "F=%~dp0acme-ledger-demo.html"
set "F=%F:\=/%"
start "" chrome --kiosk "file:///%F%?mode=kiosk" --user-data-dir="%TEMP%\demo-kiosk" --no-first-run --disable-session-crashed-bubble
