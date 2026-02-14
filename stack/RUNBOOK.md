# Stack 실행 RUNBOOK (RTX 4060 8GB, 다운 방지)

## 0. Pre-flight 체크리스트

| Check | 방법 | PASS |
|-------|------|------|
| Docker Desktop | 실행 중 확인 | `docker info` 성공 |
| 디스크 여유 | C: 드라이브 | ≥10GB |
| .env 존재 | `stack/.env` | OLLAMA_PORT, GRAFANA_* 등 설정됨 |
| 브라우저/게임 | GPU 사용 앱 | 가능한 한 종료 |

---

## 1. 단계별 실행 순서 (권장)

### Phase 1: Ollama 단독

```powershell
cd stack
docker compose up -d ollama
```

- 안정 확인: `docker compose ps`, `curl http://localhost:11434/api/tags`
- 다운 발생 시: [2. 호스트 Ollama 대안](#2-호스트-ollama-대안)으로 전환

### Phase 2: openclaw 추가

```powershell
docker compose up -d openclaw
```

- openclaw-stub 빌드 후 기동
- 헬스: `curl http://localhost:8088/healthz`

### Phase 3: 모니터링 추가

```powershell
docker compose up -d prometheus grafana
```

- Grafana: http://localhost:3000 (admin/admin)

---

## 2. 호스트 Ollama 대안

Docker 실행 시 다운이 반복되면, 프로젝트 루트에서:

```powershell
.\run-ollama.ps1 -Preset safe
```

- Docker/WSL2 오버헤드 없음
- VRAM 7GB 한도, 4k 컨텍스트

---

## 3. 문제 발생 시 대응

| 증상 | 대응 |
|------|------|
| OOM / GPU 다운 | CTX 4096→3072, 더 작은 모델(qwen2.5:7b Q4) |
| 설치 중 다운 | Phase 1만 실행, 나머지는 안정 후 추가 |
| ingest 빌드 실패 | `stack/ingest/tg`, `stack/ingest/wa` 미존재. vram.md 기반 디렉터리 생성 필요 |

---

## 4. 롤백

```powershell
docker compose down
```

---

## 5. 참조

- [README_RUN.md](README_RUN.md) - 기본 실행 요약
- [config/VRAM_계산_요약.md](../config/VRAM_계산_요약.md) - VRAM 권장값
