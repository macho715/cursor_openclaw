# 스택 세션 보고서

스택(Ollama, OpenClaw, Prometheus, Grafana) 설치·설정 및 진단 작업 내용.

---

## 1. 지금까지 작업 내용

### 1.1 다운 현상 진단

| 항목 | 내용 |
|------|------|
| 증상 | 스택 실행 시 PC 다운/재부팅 의심 |
| 조치 | 단계별 로깅 스크립트 추가 |
| 도구 | `diagnose-install.ps1`, `run-ollama-logged.cmd`, `run-phase2-logged.cmd`, `run-phase3-logged.cmd` |
| 결과 | Phase 1~3 정상 완료, 크래시 미발생 |

### 1.2 스택 실행

- **Phase 1**: ollama pull & up
- **Phase 2**: openclaw 빌드 및 기동
- **Phase 3**: prometheus, grafana 기동

### 1.3 ollama healthcheck 수정

| 변경 전 | 변경 후 |
|---------|---------|
| `wget` 기반 healthcheck | `ollama list` 기반 |
| start_period 20s | 45s |

원인: ollama 이미지에 wget 미포함 → openclaw 의존성 실패. 수정 후 정상.

### 1.4 기타 변경

- `docker-compose.yml`: `version` 제거(obsolete 경고 제거)
- `grafana/dashboards/` 디렉터리 생성
- `docker-compose.cpu.yml`: GPU 미지원 시 CPU 모드
- `check-grafana.cmd`: Grafana 상태 점검

### 1.5 다음 단계 문서화

| 파일 | 용도 |
|------|------|
| `stack/NEXT_STEPS.md` | 스택 기동 후 작업(모델 pull, Grafana, 모니터링) |
| `stack/run-next-steps.cmd` | 모델 pull 및 openclaw 검증 실행 |
| `stack/RUNBOOK.md` | 섹션 6·7에 다음 단계 링크 추가 |

### 1.6 메인 모델 변경

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| 메인 모델 | exaone3.5:7.8b | kwangsuklee/SEOKDONG-llama3.1_korean_Q5_K_M |
| 용량 | 4.8GB | 5.7GB |

수정 파일: `docker-compose.yml`, `NEXT_STEPS.md`, `run-next-steps.cmd`

### 1.7 생성·수정된 파일 목록

| 경로 | 유형 |
|------|------|
| `stack/diagnose-install.ps1` | 생성 |
| `stack/preflight-only.ps1` | 생성 |
| `stack/test-write.cmd` | 생성 |
| `stack/run-preflight.cmd` | 생성 |
| `stack/run-diagnose.cmd` | 생성 |
| `stack/run-ollama-logged.cmd` | 생성 |
| `stack/run-phase2-logged.cmd` | 생성 |
| `stack/run-phase3-logged.cmd` | 생성 |
| `stack/run-next-steps.cmd` | 생성 |
| `stack/check-grafana.cmd` | 생성 |
| `stack/docker-compose.yml` | 수정 |
| `stack/docker-compose.cpu.yml` | 생성 |
| `stack/grafana/dashboards/.gitkeep` | 생성 |
| `stack/NEXT_STEPS.md` | 생성 |
| `stack/RUNBOOK.md` | 수정 |
| `README.md` | 수정 (문서 인덱스에 STACK_SESSION_REPORT 링크) |
| `docs/STACK_SESSION_REPORT.md` | 생성 |

### 1.8 트러블슈팅 (참고)

| 증상 | 원인 | 대응 |
|------|------|------|
| Grafana localhost:3000 접속 불가 | Docker Desktop 미실행 | Docker Desktop 기동 후 `docker compose up -d` |
| ollama unhealthy → openclaw 기동 실패 | healthcheck의 wget 미지원 | `ollama list` 기반으로 변경 |
| openclaw-stub vs 호스트 OpenClaw | 모델 설정 경로 상이 | 스택: `OLLAMA_MODEL`(docker-compose). 호스트: `openclaw.json` |

### 1.9 patch3 스캐폴딩 실행 (2026-02-15)

patch3 기반 autodev-queue 스캐폴딩 적용 및 검증 완료.

**실행 흐름**

| 단계 | 명령/작업 | 결과 |
|------|-----------|------|
| 1 | 스캐폴딩 생성 | docker-compose.yml, .autodev_ssot/ 4종, scripts/, openclaw_worker/ |
| 2 | init_queue.sh | 성공 |
| 3 | docker compose up -d | ollama 컨테이너 이름 충돌로 1차 실패 |
| 4 | 워커만 기동 | `docker compose --profile worker up -d --build --no-deps openclaw-worker` |
| 5 | submit_task.sh (task_template.json) | 성공 |
| 6 | 워커 산출물 | T20260215-0001.patch, T20260215-0001.report.json |
| 7 | Gate | gate_local.sh T20260215-0001.patch → PASS |
| 8 | 감사 로그 | events.ndjson에 TASK_CLAIMED, PATCH_PROPOSED 기록 |

**트러블슈팅**

| 증상 | 원인 | 대응 |
|------|------|------|
| ollama 컨테이너 이름 충돌 | 기존 healthy ollama 이미 실행 중 | 기존 ollama 재사용, 워커만 `--no-deps`로 기동 |
| 워커 404 (모델 없음) | 기본 모델 qwen2.5-coder:7b 미설치 | `.env`에 `OLLAMA_MODEL=kwangsuklee/SEOKDONG-llama3.1_korean_Q5_K_M:latest` 설정 후 워커 재기동 |

### 1.10 Telegram 스모크 테스트 (2026-02-15)

openclaw.json Telegram 설정 검증 완료.

| 항목 | 결과 |
|------|------|
| getMe | ok=true (토큰 유효) |
| bot username | macho1901bot |
| sendMessage | ok=true |
| 대상 chat_id | 470962761 |
| message_id | 157 |

- **결과**: openclaw.json의 botToken/allowFrom 조합으로 실제 1회 수신 테스트 성공.

### 1.11 Telegram Mode B 운영 전환 (2026-02-16)

Telegram 기반 Mode B 운영 가동 + 2단 승인 흐름 구축.

| 항목 | 내용 |
|------|------|
| **Orchestrator** | `tg_orchestrator.py` — `/work`, `/status`, `/stop`, `/resume`, `/approve`, `/reject` |
| **2단 승인** | `.autodev_queue/approved/<task_id>.approved.json` 플래그 + `cursor_apply_approved.ps1` |
| **입력 품질** | WORK_TEXT_TOO_SHORT, INTENT_MISSING, TARGET_MISSING 자동 거절 |
| **트러블슈팅** | HTTP 409(중복 poller) → 단일 인스턴스만 유지, repo_clean → .gitignore 보강 |

- **문서**: `docs/MODE_B_TELEGRAM_AUTOMATION.md`, `docs/WORKLOG_2026-02-16.md`
- **커밋**: 3f8f910 (2단 승인 플로우)

---

## 2. 현재 스택 상태

| 서비스 | 상태 | URL |
|--------|------|-----|
| ollama | Healthy | http://localhost:11434 |
| openclaw | Running | http://localhost:8088/healthz |
| prometheus | Running | http://localhost:9090 |
| grafana | Running | http://localhost:3000 (admin/admin) |

**설치된 모델**

- 메인: kwangsuklee/SEOKDONG-llama3.1_korean_Q5_K_M (5.7GB)
- fallback: exaone3.5:7.8b (4.8GB)

---

## 3. 앞으로 할 작업

[stack/NEXT_STEPS.md](../stack/NEXT_STEPS.md) 참조. (모델 pull, Grafana, 전체 모니터링 프로파일, ingest, healthcheck 등)

---

## 4. 참조

- [stack/RUNBOOK.md](../stack/RUNBOOK.md) - Phase 1~3, 롤백, 진단
- [stack/NEXT_STEPS.md](../stack/NEXT_STEPS.md) - 스택 기동 후 상세
- [config/VRAM_계산_요약.md](../config/VRAM_계산_요약.md) - VRAM 권장값
- [vram.md](../vram.md) - 개발PC/WSL2 안전 러닝 아키텍처
- [ROADMAP.md](ROADMAP.md) - 시스템 전체 로드맵
