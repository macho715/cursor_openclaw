@echo off
set "LOG=%USERPROFILE%\AppData\Local\Temp\stack_diag_debug.log"
cd /d "%~dp0"

echo [1/4] Pull ollama...
echo {"event":"before_pull","time":"%date% %time%"} >> "%LOG%"
docker compose pull ollama
echo {"event":"after_pull","time":"%date% %time%"} >> "%LOG%"
echo [2/4] Pull done.

echo [3/4] Start ollama...
echo {"event":"before_up","time":"%date% %time%"} >> "%LOG%"
docker compose up -d ollama
echo {"event":"after_up","time":"%date% %time%"} >> "%LOG%"
echo [4/4] Done. Log: %LOG%

pause
