# 다음 단계 (스택 기동 후)

Phase 1~3 (ollama, openclaw, prometheus, grafana) 실행 후 수행할 작업.

---

## 1. LLM 모델 Pull

openclaw가 `OLLAMA_MODEL=kwangsuklee/SEOKDONG-llama3.1_korean_Q5_K_M`(메인)를 사용. 모델을 pull해야 실제 추론 가능.

```cmd
docker exec ollama ollama pull kwangsuklee/SEOKDONG-llama3.1_korean_Q5_K_M
```

- 용량: 약 5.7GB (RTX 4060 8GB 기준 OK) — [config/VRAM_계산_요약.md](../config/VRAM_계산_요약.md)
- OOM 시: CTX 4096→3072 하향. fallback: `exaone3.5:7.8b`

---

## 2. openclaw 검증

```cmd
curl http://localhost:8088/healthz
```

모델 pull 후 openclaw가 첫 요청 시 모델 로드. 응답 지연 발생 가능.

---

## 3. Grafana 설정

- 접속: http://localhost:3000 (admin/admin)
- Prometheus datasource: 프로비저닝됨 (`grafana/provisioning/datasources/datasource.yml`)
- 대시보드: `grafana/dashboards/` 또는 수동 추가

---

## 4. (선택) 전체 모니터링 프로파일

cadvisor, node-exporter, dcgm-exporter 포함:

```cmd
docker compose --profile full up -d
```

- cadvisor: http://localhost:8080
- node-exporter: http://localhost:9100
- dcgm-exporter: http://localhost:9400

---

## 5. (선택) ingest 서비스

tg-ingest, wa-ingest 사용 시:

- `stack/ingest/tg`, `stack/ingest/wa` 디렉터리 및 Dockerfile 필요
- `.env`에 TG_BOT_TOKEN, TG_ALLOWED_CHAT_IDS, WA_CLIENT_ID 등 설정

```cmd
docker compose --profile ingest up -d
```

---

## 참조

- [RUNBOOK.md](RUNBOOK.md) - Phase 1~3, 롤백, 진단
- [config/VRAM_계산_요약.md](../config/VRAM_계산_요약.md) - VRAM 권장값
- [vram.md](../vram.md) - 개발PC/WSL2 안전 러닝 아키텍처
