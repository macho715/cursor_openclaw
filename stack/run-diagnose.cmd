@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0diagnose-install.ps1"
echo Check logs: .cursor\debug.log or %USERPROFILE%\AppData\Local\Temp\stack_diag_debug.log
pause
