# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) where applicable.

---

## [Unreleased]

### Fixed

- `AuditLogger.append_event`를 파일 배타 락 임계구역으로 변경해 `verify_integrity -> prev_hash 계산 -> append`를 원자적으로 수행하고, 락 획득 후 최신 파일 재읽기로 stale read를 방지함.
- 동일 audit 로그 파일에 대한 멀티스레드/멀티프로세스 동시 append 테스트를 추가하고, 완료 후 `verify_integrity()` 통과를 검증함.

---

## [0.1.0] - 2026-02-14

### Added

- **Folder Queue Option A** 정책·레일: Cursor(Control-Plane) + OpenClaw(Worker) 무인 자동개발 흐름.
- **AGENTS.md**: 에이전트 실행 규칙 SSOT(권한/Queue/ Gate/Decision/감사/복구).
- **MANIFEST.json**: 프로젝트명, `stage_current`(3), `stage_next`(4), `baton_file`.
- **BATON_CURRENT.md**: Stage 3 → 4 요약(문서/설정 → 코드 구현 전달).
- **config/policy**: CURSOR_RULES, TOOL_POLICY, APPROVAL_MATRIX, AUDIT_LOG_SCHEMA, RESOURCE_LIMITS, LLM_PERFORMANCE_GATES.
- **config/uiux**: UX_FLOW, SCREENS, INPUT_GUARD, A11Y_DoD, COPY, COMPONENTS.
- **.cursor/commands** (8종): `/setup:init`, `/queue:claim`, `/queue:open-plan`, `/queue:request-patch-draft`, `/queue:run-gates`, `/queue:decide`, `/queue:pr-merge`, `/incident:recover`.
- **.cursor/rules**: 000-core, 010-folder-queue, 020-gates-and-decision, 030-audit-append-only, 040-external-io-stop, 050-ux-a11y, AUTODEV_POLICY.
- **.cursor/skills**: stop-check, claim-lock, intake-validate, queue-scan, patch-draft-request, patch-review, diff-risk-scan, gate-runner, decision-router, audit-append, pr-merge-orchestrator, incident-brief 등.
- **.cursor/agents**: orchestrator, queue-sentinel, gate-runner, audit-scribe, verifier.
- **README.md**: Exec, Visual(S1~S7), 시스템 아키텍처 요약, 주요 문서 인덱스, SSOT, allowlist, 폴더 구조, Option A/B/C, 로드맵·변경 이력 참조, 빠른 시작.
- **docs/ARCHITECTURE.md**: 역할·권한, Folder Queue, 안전 흐름(Mermaid), Gate 파이프라인, Decision, 화면 S1~S7, 정책 SSOT, 커맨드·스킬, 감사·STOP, 참조 링크.
- **CHANGELOG.md**: 본 변경 이력 문서.

### Security

- STOP(킬스위치) 우선, allowlist·민감정보(토큰/키/내부 URL) 정책, append-only 감사 로그 고정.

---

[Unreleased]: https://github.com/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/releases/tag/v0.1.0
