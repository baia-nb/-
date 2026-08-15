@echo off
cd /d "%~dp0"
if not exist cloudflared.exe (
  echo Download cloudflared.exe into this scripts folder first:
  echo https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe
  pause
  exit /b 1
)
REM start local backend (safe to ignore if port 8000 already in use)
start "" /D "%~dp0.." "C:\Users\ttnld\.workbuddy\binaries\python\versions\3.13.12\python.exe" -m uvicorn web.backend.main:app --port 8000 --log-level warning
set /p TOK=<cloudflared_token.txt
cloudflared.exe tunnel run --token %TOK% --url http://localhost:8000 --protocol http2
