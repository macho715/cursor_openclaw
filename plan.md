
# plan.md (SoT) — Stage 3 Cursor Project Setting

## 목표
- Folder Queue(.autodev_queue) 상태 전이를 **정책/규칙으로 강제**
- OpenClaw(제안) / Cursor(적용) 권한 분리 + Approve-to-Run 고정
- DRY_RUN→Diff→Gate→Decision→APPLY + STOP(킬스위치) + append-only 감사로그 고정

## Stage 3 작업 큐(체크리스트)
- [ ] `.cursor/rules/*.mdc` (코어/큐/게이트/감사/외부IO/UX-A11y)
- [ ] `.cursor/commands/*.md` (S1~S7 흐름 명령)
- [ ] `.cursor/agents/*.md` (Orchestrator/Sentinel/GateRunner/AuditScribe/Verifier)
- [ ] `.cursor/skills/*/SKILL.md` (queue-intake/patch-review/gate-execution/audit-append-only/incident-stop)
- [ ] `config/policy/*` 4종 (CURSOR_RULES/TOOL_POLICY/APPROVAL_MATRIX/AUDIT_LOG_SCHEMA)
- [ ] `config/uiux/*` 6종 (UX_FLOW/SCREENS/INPUT_GUARD/A11Y_DoD/COPY/COMPONENTS)
- [ ] CI/Pre-commit (ci.yml, .pre-commit-config.yaml, pyproject.toml)
- [ ] DRY_RUN 검증 (pytest, pre-commit)

## 완료(Pilot, 2026-02)
- [x] Telegram Mode B Orchestrator (`tg_orchestrator.py`, `/work`, `/approve`, `/reject`)
- [x] 2단 승인 플로우 (`cursor_apply_approved.ps1`, `.autodev_queue/approved/`)
- [x] `docs/MODE_B_OPERATION_RUNBOOK.md`, `docs/MODE_B_TELEGRAM_AUTOMATION.md`
- [x] `docs/WORKLOG_2026-02-16.md`

## 다음 작업
- [ ] `/approve` 이후 승인파일 기반 자동 PR 브랜치 생성(로컬만, push 금지) 옵션
- [ ] `/work` 프롬프트 템플릿에 작업별 스키마(파일/라인 제한) 강제
- [ ] 승인/거절 이벤트 대시보드용 audit 집계 스크립트 확장

## Stage 3 Exit 판정
- Go: 위 항목 전부 완료 + CI/Pre-commit 통과
- Revise: 정책/게이트/복구 책임 분리 모호
- Stop: allowlist/보안 정책 불명확 또는 외부전송 우회 허용
