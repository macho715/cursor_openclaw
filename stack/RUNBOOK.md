# Stack 실행 RUNBOOK (RTX 4060 8GB, 다운 방지)

**처음 설치**: Docker·WSL2·Ollama가 아직 없다면 → [Docker-OpenClaw-설치-가이드.md](../Docker-OpenClaw-설치-가이드.md)  
**상세 옵션·트러블슈팅**: [DOCKER-실행-가이드.md](../DOCKER-실행-가이드.md)

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

## 5. 다운 진단 (로그 기반 원인 추적)

**재현 시 반드시 아래 순서로 실행** (로그가 없으면 원인 추적 불가):

1. **CMD에서 테스트** (PowerShell/Docker 없음):
   ```
   cd /d c:\Users\jichu\Downloads\cursor_full_setting_optionA\stack
   echo [%date% %time%] test >> %USERPROFILE%\AppData\Local\Temp\stack_test.txt
   type %USERPROFILE%\AppData\Local\Temp\stack_test.txt
   ```
   → `stack_test.txt`가 생성되어야 함. 없으면 CMD/TEMP 경로 문제.

2. **Ollama 로그 래퍼 실행**: `run-ollama-logged.cmd` 더블클릭
   → 다운 후 `%USERPROFILE%\AppData\Local\Temp\stack_diag_debug.log` 확인
   → `before_pull` / `after_pull` / `before_up` / `after_up` 중 마지막 항목이 크래시 직전 단계

3. **진단 스크립트** (PowerShell): `run-diagnose.cmd` 또는 `.\diagnose-install.ps1`
   → `.cursor\debug.log`, `%TEMP%\stack_diag_debug.log` 에 NDJSON 기록

---

## 6. 다음 단계

Phase 1~3 완료 후: 모델 pull, openclaw 검증, Grafana 설정. `run-next-steps.cmd` 실행 또는 [NEXT_STEPS.md](NEXT_STEPS.md) 참조.

---

## 7. 기본·옵션 실행 요약

- **최소(다운 방지)**: `docker compose up -d ollama` → 안정 후 `docker compose up -d openclaw prometheus grafana`
- **전체 한번에**: `docker compose up -d` (ollama, openclaw, prometheus, grafana)
- **전체 모니터링**: `docker compose --profile full up -d` (cadvisor, node-exporter, dcgm-exporter)
- **ingest**: `docker compose --profile ingest up -d` (stack/ingest/tg, wa 필요)

**변경 사항**: OLLAMA_CONTEXT_LENGTH 8192→4096, OLLAMA_NUM_PARALLEL 1, dcgm/cadvisor/node-exporter는 `full` 프로파일, tg/wa-ingest는 `ingest` 프로파일.

---

## 8. 참조

- [README_RUN.md](README_RUN.md) - RUNBOOK 빠른 요약
- [NEXT_STEPS.md](NEXT_STEPS.md) - 스택 기동 후 상세
- `run-next-steps.cmd` - 모델 pull + openclaw 검증
- `run-ollama-logged.cmd` - Phase1 로깅
- `run-phase2-logged.cmd` - Phase2 (openclaw) 로깅
- `run-phase3-logged.cmd` - Phase3 (prometheus, grafana) 로깅
- [config/VRAM_계산_요약.md](../config/VRAM_계산_요약.md) - VRAM 권장값
- [run-ollama.ps1](../run-ollama.ps1) - 호스트 Ollama (섹션 2 대안)
