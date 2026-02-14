@echo off
cd /d "%~dp0"

echo [1/3] Pull LLM model (SEOKDONG-llama3.1_korean_Q5_K_M)...
docker exec ollama ollama pull kwangsuklee/SEOKDONG-llama3.1_korean_Q5_K_M

echo.
echo [2/3] Verify openclaw...
curl -sf http://localhost:8088/healthz >nul 2>&1 && echo openclaw OK || echo openclaw not ready - check: curl http://localhost:8088/healthz

echo.
echo [3/3] Grafana: http://localhost:3000 (admin/admin)
echo See NEXT_STEPS.md for optional full monitoring and ingest.

pause
