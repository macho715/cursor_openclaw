# 스택 사용법

Ollama, openclaw-stub, Prometheus, Grafana 실행 후 사용 방법.

---

## 1. 스택 개요

| 서비스 | 용도 | 접속 URL |
|--------|------|-----------|
| Ollama | LLM (로컬 모델) | http://localhost:11434 |
| openclaw-stub | API/healthz (모니터링용) | http://localhost:8088 |
| Prometheus | 메트릭 수집 | http://localhost:9090 |
| Grafana | 대시보드 | http://localhost:3000 (admin/admin) |
| cadvisor | 컨테이너 메트릭 | http://localhost:8080 (full 프로파일) |
| node-exporter | 호스트 메트릭 | http://localhost:9100 (full 프로파일) |

---

## 2. 기본 사용 흐름

### 2.1 스택 기동

```powershell
cd stack
docker compose up -d
```

### 2.2 모델 Pull (최초 1회)

```powershell
docker exec ollama ollama pull kwangsuklee/SEOKDONG-llama3.1_korean_Q5_K_M
```

### 2.3 상태 확인

```powershell
curl http://localhost:8088/healthz   # openclaw-stub
curl http://localhost:11434/api/tags # Ollama 모델 목록
```

---

## 3. Ollama 직접 사용

### 3.1 CLI 채팅

```powershell
ollama run kwangsuklee/SEOKDONG-llama3.1_korean_Q5_K_M
# 또는 fallback
ollama run exaone3.5:7.8b
```

### 3.2 API 호출

```powershell
Invoke-RestMethod -Uri "http://localhost:11434/api/generate" -Method Post `
  -ContentType "application/json" `
  -Body '{"model":"kwangsuklee/SEOKDONG-llama3.1_korean_Q5_K_M","prompt":"안녕","stream":false}'
```

---

## 4. openclaw-stub vs OpenClaw Gateway

| 항목 | openclaw-stub (현재 스택) | OpenClaw Gateway |
|------|---------------------------|------------------|
| 역할 | healthz/API placeholder | WebChat UI, 에이전트 |
| UI | 없음 | 있음 (http://127.0.0.1:18789) |
| 실행 | `docker compose up -d openclaw` | `openclaw gateway` (별도 설치) |
| LLM | 연동 없음 | Ollama 직접 연결 |

**채팅 UI가 필요하면** → OpenClaw Gateway를 별도 설치. Ollama에 직접 연결하며 openclaw-stub과는 무관.

---

## 5. Grafana 사용

- **접속**: http://localhost:3000
- **로그인**: admin / admin
- **데이터소스**: Prometheus 프로비저닝됨
- **대시보드**: `stack/grafana/dashboards/` 또는 수동 Import

---

## 6. 자주 쓰는 명령

```powershell
# 스택 기동
cd stack
docker compose up -d

# 전체 모니터링 (cadvisor, node-exporter, dcgm-exporter)
docker compose --profile full up -d

# 롤백
docker compose down

# 컨테이너 상태
docker compose ps

# Ollama 모델 목록
docker exec ollama ollama list

# openclaw-stub 헬스
curl http://localhost:8088/healthz
```

---

## 7. 참조

- [stack/RUNBOOK.md](../stack/RUNBOOK.md) - Phase 1~3, 롤백, 진단
- [stack/NEXT_STEPS.md](../stack/NEXT_STEPS.md) - 기동 후 작업
- [docs/OLLAMA_OPENCLAW_USAGE.md](OLLAMA_OPENCLAW_USAGE.md) - OpenClaw Gateway 사용법
- [docs/OPENCLAW_OLLAMA_WINDOWS_SUMMARY.md](OPENCLAW_OLLAMA_WINDOWS_SUMMARY.md) - OpenClaw+Ollama 설치 요약
