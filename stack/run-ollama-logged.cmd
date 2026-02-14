@echo off
set "LOG=%USERPROFILE%\AppData\Local\Temp\stack_diag_debug.log"
cd /d "%~dp0"

echo {"event":"before_pull","time":"%date% %time%"} >> "%LOG%"
docker compose pull ollama
echo {"event":"after_pull","time":"%date% %time%"} >> "%LOG%"

echo {"event":"before_up","time":"%date% %time%"} >> "%LOG%"
docker compose up -d ollama
echo {"event":"after_up","time":"%date% %time%"} >> "%LOG%"

echo Log: %LOG%
pause
