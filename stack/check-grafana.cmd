@echo off
cd /d "%~dp0"
echo === Docker containers ===
docker compose ps
echo.
echo === Grafana container logs (last 20 lines) ===
docker compose logs --tail=20 grafana
echo.
echo === Port 3000 check ===
netstat -ano | findstr ":3000"
echo.
echo If grafana exited, run: docker compose up -d grafana
pause
