@echo off
set "LOG=%USERPROFILE%\AppData\Local\Temp\stack_diag_debug.log"
cd /d "%~dp0"

echo [Phase 3] prometheus + grafana
echo.
echo [1/2] Start monitoring...
echo {"event":"phase3_before_monitoring","time":"%date% %time%"} >> "%LOG%"
docker compose up -d prometheus grafana
echo {"event":"phase3_after_monitoring","time":"%date% %time%"} >> "%LOG%"
echo [2/2] Done. Grafana: http://localhost:3000 (admin/admin)
echo Log: %LOG%

pause
