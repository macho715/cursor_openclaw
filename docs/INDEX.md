# 문서 인덱스

프로젝트 전체 문서 마스터 네비게이션.

---

## 역할별 읽기 경로

### 신규 설치자

**설치 흐름**: Docker-OpenClaw-설치-가이드 → DOCKER-실행-가이드 → RUNBOOK

1. [Docker-OpenClaw-설치-가이드.md](../Docker-OpenClaw-설치-가이드.md) - Docker·WSL2·Ollama 처음부터 설치
2. [DOCKER-실행-가이드.md](../DOCKER-실행-가이드.md) - 상세 옵션·트러블슈팅
3. [stack/RUNBOOK.md](../stack/RUNBOOK.md) - Phase 1~3 실행
4. [stack/NEXT_STEPS.md](../stack/NEXT_STEPS.md) - 모델 pull, Grafana

**OpenClaw+Ollama 상세**: [OPENCLAW_OLLAMA_WINDOWS_SUMMARY.md](OPENCLAW_OLLAMA_WINDOWS_SUMMARY.md), [OLLAMA_OPENCLAW_USAGE.md](OLLAMA_OPENCLAW_USAGE.md), [올라마세팅.md](../올라마세팅.md)

### 스택 운영자

- [stack/RUNBOOK.md](../stack/RUNBOOK.md) - Phase별 실행, 롤백, 진단
- [docs/STACK_USAGE.md](STACK_USAGE.md) - 스택 사용법 (접속 URL, 명령, openclaw-stub vs Gateway)
- [stack/NEXT_STEPS.md](../stack/NEXT_STEPS.md) - 기동 후 작업
- [docs/STACK_SESSION_REPORT.md](STACK_SESSION_REPORT.md) - 작업 이력·트러블슈팅
- [docs/SESSION_WORK_REPORT.md](SESSION_WORK_REPORT.md) - 세션 작업 보고 (최근 작업 요약)
- [config/VRAM_계산_요약.md](../config/VRAM_계산_요약.md) - VRAM 권장값

### 정책·아키텍처 담당

- [AGENTS.md](../AGENTS.md) - 에이전트 SSOT (README보다 우선)
- [docs/ARCHITECTURE.md](ARCHITECTURE.md) - 시스템 아키텍처
- [docs/ROADMAP.md](ROADMAP.md) - Prepare→Pilot→Build→Operate→Scale
- [config/policy/](../config/policy/) - CURSOR_RULES, TOOL_POLICY, APPROVAL_MATRIX, AUDIT_LOG_SCHEMA
- [config/uiux/](../config/uiux/) - UX_FLOW, SCREENS, INPUT_GUARD, A11Y_DoD, COPY, COMPONENTS

---

## 문서별 목록

| 문서 | 용도 |
|------|------|
| [README.md](../README.md) | 프로젝트 요약, Exec, 화면 7개 |
| [AGENTS.md](../AGENTS.md) | 에이전트 실행 규칙 SSOT |
| [MANIFEST.json](../MANIFEST.json) | 프로젝트명, stage |
| [BATON_CURRENT.md](../BATON_CURRENT.md) | 현재 Stage 요약 |
| [CHANGELOG.md](../CHANGELOG.md) | 변경 이력 |
| [Docker-OpenClaw-설치-가이드.md](../Docker-OpenClaw-설치-가이드.md) | Docker OpenClaw 설치 (처음부터) |
| [DOCKER-실행-가이드.md](../DOCKER-실행-가이드.md) | Docker 상세 옵션·트러블슈팅 |
| [vram.md](../vram.md) | 개발PC/WSL2 안전 러닝 아키텍처 |
| [올라마세팅.md](../올라마세팅.md) | run-ollama.ps1 상세, 호스트 Ollama |
| [docs/ARCHITECTURE.md](ARCHITECTURE.md) | 시스템 아키텍처 |
| [docs/ROADMAP.md](ROADMAP.md) | 로드맵 |
| [docs/STACK_SESSION_REPORT.md](STACK_SESSION_REPORT.md) | 스택 작업 이력·앞으로 할 일 |
| [docs/SESSION_WORK_REPORT.md](SESSION_WORK_REPORT.md) | 세션 작업 보고 (최근 작업 요약) |
| [docs/MODE_B_OPERATION_RUNBOOK.md](MODE_B_OPERATION_RUNBOOK.md) | Mode B(Claude=티켓+diff) 운영·Gate·allowlist |
| [docs/STACK_USAGE.md](STACK_USAGE.md) | 스택 사용법 (접속, 명령, openclaw-stub vs Gateway) |
| [docs/OPENCLAW_OLLAMA_WINDOWS_SUMMARY.md](OPENCLAW_OLLAMA_WINDOWS_SUMMARY.md) | OpenClaw+Ollama Windows 설치 요약 |
| [docs/OLLAMA_OPENCLAW_USAGE.md](OLLAMA_OPENCLAW_USAGE.md) | Ollama/OpenClaw 사용법 |
| [stack/RUNBOOK.md](../stack/RUNBOOK.md) | 스택 Phase 1~3, 롤백, 진단 |
| [stack/README_RUN.md](../stack/README_RUN.md) | RUNBOOK 빠른 요약 |
| [stack/NEXT_STEPS.md](../stack/NEXT_STEPS.md) | 스택 기동 후 (모델 pull, Grafana) |
| [config/VRAM_계산_요약.md](../config/VRAM_계산_요약.md) | VRAM 계산·세팅 |
| [config/policy/](../config/policy/) | 정책 문서 |
| [config/uiux/](../config/uiux/) | UI/UX 스펙 |
| [run-ollama.ps1](../run-ollama.ps1) | 호스트 Ollama 실행 (RUNBOOK "호스트 Ollama 대안" 참조) |
