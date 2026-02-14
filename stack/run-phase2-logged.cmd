@echo off
set "LOG=%USERPROFILE%\AppData\Local\Temp\stack_diag_debug.log"
cd /d "%~dp0"

echo [Phase 2] openclaw (Ollama model load may trigger VRAM spike)
echo.
echo [1/2] Start openclaw...
echo {"event":"phase2_before_openclaw","time":"%date% %time%"} >> "%LOG%"
docker compose up -d openclaw
echo {"event":"phase2_after_openclaw","time":"%date% %time%"} >> "%LOG%"
echo [2/2] Done. Log: %LOG%

echo.
echo Wait ~30s for openclaw health, then: curl http://localhost:8088/healthz
pause
