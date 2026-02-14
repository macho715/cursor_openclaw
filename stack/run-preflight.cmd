@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0preflight-only.ps1"
echo Check: %USERPROFILE%\AppData\Local\Temp\stack_diag_debug.log
pause
