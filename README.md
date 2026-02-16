# Cursor(Control-Plane) + OpenClaw(Worker) "무인 자동개발" — Full Setting Pack (PROPOSED)

## Exec (3–5줄)

- **Folder Queue 상태머신(inbox→claimed→work→pr→done/blocked)**만 허용해 입력·진행·종료를 **정책으로 강제**.
- **OpenClaw=diff/patch 제안만**, **Cursor=APPLY/TEST/COMMIT/PR/MERGE 소유**로 권한 분리 + **Approve-to-Run** 강제.
- 안전 흐름: **DRY_RUN → Diff → Gate → Decision(AUTO_MERGE/PR_ONLY/ZERO_STOP) → APPLY**, STOP(킬스위치) 감지 시 즉시 중단·격리.
- WebChat/외부전송은 우회 경로로 간주해 기본 비활성/읽기전용, 모든 상태 변경은 **append-only 감사로그**로 기록.

---

## Visual — 화면 7개 고정 요약

| ID | Screen | 목적 | 주요 가드(정책) | Primary CTA |
|---|---|---|---|---|
| S1 | Queue Monitor | 큐 상태/STOP/요약 KPI | STOP 즉시 차단, claimed 락 충돌 표시 | Claim Task |
| S2 | Task Detail | task/acceptance/risk/allowlist/commands 확인 | 필수 입력 누락 시 진행 불가 | Open Plan |
| S3 | Plan | 범위/테스트/롤백/리스크 정리 | 보호구역/외부전송 금지 고정 | Request Patch Draft |
| S4 | Patch Diff | OpenClaw 제안 diff 전용 뷰 | 라인수/삭제/lockfile/allowlist 스캔 | Run Gates |
| S5 | Gate Results | Gate PASS/FAIL + Evidence | FAIL 시 PR_ONLY 또는 ZERO_STOP | Decide |
| S6 | PR & Merge | PR 생성/상태체크/Auto-merge 조건 | AUTO_MERGE 조건 불충족=PR_ONLY | Create PR / Merge |
| S7 | Incident | ZERO_STOP/FAIL 로그·복구 | 재시도/롤백/운영자 알림 | Recover / Rollback |

---

## 시스템 아키텍처(요약)

- **역할**: Cursor = Control-Plane(APPLY/테스트/커밋/PR/머지), OpenClaw = Worker(diff·patch 제안만), Operator = 최종 승인·STOP 해제.
- **Queue**: `.autodev_queue/` — inbox → claimed → work → pr → done(정상), blocked(격리), audit(감사로그), STOP(킬스위치).
- **Gate**: G0(STOP) ~ G6(append-only) + REMOTE_GATE; Decision = AUTO_MERGE / PR_ONLY / ZERO_STOP.
- 상세: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [AGENTS.md](./AGENTS.md) 참조.

---

## 주요 문서 인덱스

| 문서 | 용도 |
|------|------|
| [docs/INDEX.md](docs/INDEX.md) | 전체 문서 마스터 네비게이션(역할별 읽기 경로) |
| `AGENTS.md` | 에이전트 실행 규칙 SSOT(README보다 우선) |
| `MANIFEST.json` | 프로젝트명, stage_current/stage_next, baton_file |
| `BATON_CURRENT.md` | 현재 Stage 요약(예: Stage 3 → 4) |
| `docs/CLAUDE_CODE_OLLAMA_WINDOWS_RUNBOOK.md` | Windows 기준 Claude Code + Ollama 설치/연동/운영 런북 |
| `docs/MODE_B_OPERATION_RUNBOOK.md` | Mode B(Claude=티켓+diff) 운영·Gate·allowlist |
| `docs/WORKLOG_2026-02-15.md` | 이번 세션 작업 이력/검증 결과 |
| `docs/WORKLOG_2026-02-16.md` | Telegram Mode B 운영 전환, Orchestrator, 2단 승인 |
| `docs/MODE_B_TELEGRAM_AUTOMATION.md` | Telegram 2단 승인 자동화 Full Pack |
| `docs/NEXT_PLAN.md` | 다음 단계 실행 계획 |
| `README_AUTODEV.md` | Queue 기반 운영 절차(Worker는 diff-only, Cursor만 apply/test/commit) |
| `config/policy/*.md` | CURSOR_RULES, TOOL_POLICY, APPROVAL_MATRIX, AUDIT_LOG_SCHEMA |
| `config/uiux/*.md` | UX_FLOW, SCREENS, INPUT_GUARD, A11Y_DoD, COPY, COMPONENTS |
| `.cursor/rules/AUTODEV_POLICY.md` | Cursor 규칙 요약 |
| `.cursor/commands/*.md` | /setup:init, /queue:claim, /queue:open-plan, /queue:request-patch-draft, /queue:run-gates, /queue:decide, /queue:pr-merge, /incident:recover |
| `docs/STACK_SESSION_REPORT.md` | 스택(ollama/openclaw) 작업 이력 |
| `stack/RUNBOOK.md` | 스택 Phase 1~3 실행·롤백·진단 |
| `stack/NEXT_STEPS.md` | 스택 기동 후 작업(모델 pull, Grafana) |

---

## SSOT(읽는 순서)

1. `config/policy/CURSOR_RULES.md`
2. `config/policy/TOOL_POLICY.md`
3. `config/policy/APPROVAL_MATRIX.md`
4. `config/policy/AUDIT_LOG_SCHEMA.md`
5. `config/uiux/*` (UX_FLOW, SCREENS, INPUT_GUARD, A11Y_DoD, COPY, COMPONENTS)

---

## 경로 정책(allowlist)

- **허용**: `.cursor/`, `.github/`, `config/`, `orchestrator/`, `docs/`, `tools/`, `tests/`, `pyproject.toml`, `plan.md`, `CODEOWNERS`, `README.md`, `MANIFEST.json`, `BATON_CURRENT.md`
- UI/UX 문서의 `docs/policy/*`는 **`config/policy/*`** 로 통일.

---

## 폴더 구조 요약

| 경로 | 설명 |
|------|------|
| `.autodev_queue/` | Folder Queue(inbox/claimed/work/pr/done/blocked/audit, STOP) |
| `.cursor/` | rules, commands, skills, agents, config |
| `config/` | policy, uiux, project_profile, WORK_AUTODEV_CONFIG 등 |
| `orchestrator/` | tg_orchestrator.py, main.py, prompts, utils |
| `docs/` | ARCHITECTURE, ROADMAP, INDEX, MODE_B_TELEGRAM, WORKLOG 등 |
| `stack/` | RUNBOOK, NEXT_STEPS, docker-compose |
| `tools/` | 스크립트(예: init_autodev_queue) |
| `tests/` | 테스트 |

---

## 정책 옵션(Option A/B/C)

| 옵션 | 정책 | 처리 |
|------|------|------|
| **A(기본)** | 저위험 AUTO_MERGE 허용(조건 충족 시) | 무인 처리↑, 게이트 운영 필요 |
| B | PR_ONLY 기본(자동머지 거의 금지) | 사람 리뷰 강제 |
| C | 전부 ZERO_STOP(운영자 개입 전제) | 최대 안전, 생산성↓ |

---

## 로드맵

Prepare → Pilot → Build → Operate → Scale. KPI·기간은 [AGENTS.md](./AGENTS.md) §11, [docs/ROADMAP.md](docs/ROADMAP.md) 참조.

---

## 변경 이력

최근 변경은 `CHANGELOG.md` 참조.

---


## CLI 실행

`tools/cli.py`는 import 시 `sys.path`를 변경하지 않습니다. CLI는 패키지 실행으로 사용하세요.

```bash
python -m tools.cli --help
```

직접 스크립트 실행(`python tools/cli.py ...`)도 동작하지만, 기본 권장 경로는 `python -m tools.cli`입니다.

---

## 빠른 시작(권장: DRY_RUN)

```bash
python tools/init_autodev_queue.py --dry-run
# 승인 후
python tools/init_autodev_queue.py --apply
```
