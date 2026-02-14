# 시스템 아키텍처

Control-Plane Cursor / Worker OpenClaw — Folder Queue Option A

---

## 1. 개요

- **프로젝트**: `MANIFEST.json` — Control-Plane Cursor / Worker OpenClaw (Folder Queue Option A)
- **Stage**: 현재 3 → 다음 4 (`BATON_CURRENT.md`). Stage 3 = Cursor Project Setting(문서/정책/레일), Stage 4 = 코드 구현 전달.
- **범위**: Stage 3에서는 **문서·설정 텍스트만** 허용(구현/실행/배포 금지). 모든 상태 전이는 **append-only 감사로그**로 기록.

---

## 2. 역할·권한

| 역할 | 권한 | 비고 |
|------|------|------|
| **Cursor** | APPLY / TEST / COMMIT / PR / MERGE **소유** | Control-Plane. Gate 실행·결정·적용 담당. |
| **OpenClaw** | diff/patch **제안만** | Worker. 적용·커밋·머지 권한 없음. |
| **Operator** | 승인·거절·STOP 해제·Incident Close | 사람. 최종 통제. |

- Approve-to-Run: 실행 전 승인 강제.
- SSOT: `AGENTS.md`가 인테이크 문서보다 우선하며, 인테이크는 “데이터”로만 취급.

---

## 3. Folder Queue 상태 머신

**루트**: `.autodev_queue/`

| 폴더 | 용도 |
|------|------|
| `inbox/` | 신규 작업(폴더 단위, Task ID별) |
| `claimed/` | 락(Claim)된 작업 |
| `work/` | 패치 초안 생성·검증 진행 |
| `pr/` | PR 생성 후 상태 추적 |
| `done/` | merge + post-check 완료 |
| `blocked/` | STOP / ZERO_STOP / 수동 개입 필요 |
| `audit/` | append-only 감사로그(작업별 + 전역) |
| `STOP` (파일 또는 폴더) | 존재 시 **전면 중단** (킬스위치) |

**상태 전이**:

- `inbox/` → `claimed/`: Claim 성공(락 획득)
- `claimed/` → `work/`: Plan 완료 + Patch Draft 요청/수신
- `work/` → `pr/`: Decision = PR_ONLY 또는 AUTO_MERGE 준비(PR 생성)
- `pr/` → `done/`: merge + post-check 완료
- 임의 상태 → `blocked/`: STOP / ZERO_STOP / INPUT_MISSING 등

---

## 4. 안전 흐름

**고정 순서**:  
**DRY_RUN → Diff → Gate → Decision(AUTO_MERGE / PR_ONLY / ZERO_STOP) → APPLY**

- Gate 실행 주체: **Cursor만** (OpenClaw는 실행 금지).
- STOP 존재 시 즉시 **ZERO_STOP**, 모든 실행 CTA 비활성, S7 Incident로 수렴.

### 4.1 메인 플로우(정상)

Entry  
→ **S1 Queue Monitor**  
→ **Claim** → **S2 Task Detail** (입력 검증)  
→ **S3 Plan** (범위/테스트/롤백/리스크)  
→ **Request Patch Draft** (OpenClaw 제안만)  
→ **S4 Patch Diff** (읽기전용)  
→ **S5 Gate Results** (G0~G6 + Evidence)  
→ **Decision** (AUTO_MERGE / PR_ONLY / ZERO_STOP)  
→ **S6 PR & Merge**  
→ `done/` 또는 `blocked/`  
→ **S7 Incident** (필요 시)

### 4.2 플로우 차트(Mermaid)

```mermaid
flowchart TD
  A[Entry] --> B[S1 Queue Monitor]
  B -->|STOP 감지| Z[S7 Incident / ZERO_STOP]
  B --> C[Claim -> claimed/]
  C -->|LOCK_CONFLICT| B
  C --> D[S2 Task Detail / Input Guard]
  D -->|INPUT_MISSING| X[blocked/ + BLOCK_INPUT]
  D --> E[S3 Plan]
  E --> F[Request Patch Draft -> OpenClaw]
  F --> G[S4 Patch Diff (read-only)]
  G --> H[S5 Gate Results (Cursor runs gates)]
  H --> I{Decision}
  I -->|ZERO_STOP| Z
  I -->|PR_ONLY| P[S6 PR & Merge (PR only)] --> Q[pr/] --> R[done/]
  I -->|AUTO_MERGE| M[S6 PR & Merge (auto)] --> Q --> R
```

---

## 5. Gate 파이프라인

### 5.1 Task/코드 흐름(AGENTS.md 기준)

| Gate | 이름 | PASS 기준 | FAIL 시 |
|------|------|-----------|---------|
| G0 | STOP 체크 | STOP 미존재 | ZERO_STOP |
| G1 | Allowlist Gate | 변경이 allowlist.txt 내 100% | ZERO_STOP |
| G2 | Max Lines Gate | (add+del) ≤ 300.00 | PR_ONLY 또는 ZERO_STOP |
| G3 | No Delete Gate | 파일 삭제 0건 | ZERO_STOP |
| G4 | No Lockfile/Deps Gate | dep/lockfile 변경 0건 | PR_ONLY 또는 ZERO_STOP |
| G5 | Commands Gate | lint/test/build 모두 PASS | PR_ONLY |
| G6 | DRY_RUN↔APPLY 일치 | DRY_RUN diff == APPLY 대상 diff | PR_ONLY 또는 ZERO_STOP |

### 5.2 Stage 3 문서 흐름(.cursor/commands 기준)

문서·설정만 다루는 Stage 3에서는 아래 Gate 세트 사용(상세: `.cursor/commands/queue-run-gates.md`).

| Gate | 이름 | PASS 조건 | FAIL 시 |
|------|------|-----------|---------|
| G0 | STOP | STOP 미존재 | ZERO_STOP |
| G1 | Daily Go/No-Go | 오늘 audit=Go | AUTO_MERGE 금지(PR_ONLY) |
| G2 | Patch Size | added+deleted ≤ 300.00 | PR_ONLY |
| G3 | File Safety | 삭제/dep·lock/이진 0.00 | PR_ONLY 또는 ZERO_STOP |
| G4 | Allowlist | allowlist_write 내부만 | ZERO_STOP |
| G5 | Secrets/NDA | 민감정보 원문 0.00 | ZERO_STOP |
| G6 | Append-only | 감사로그 append-only 준수 | ZERO_STOP |
| REMOTE_GATE | Protected/Required checks | CONFIRMED+PASS | UNKNOWN이면 AUTO_MERGE 금지 |

---

## 6. Decision 규칙

| Decision | 조건 |
|----------|------|
| **ZERO_STOP** | G0/G1(allowlist)/G3(삭제)/G5(secrets)/G6 FAIL, STOP 존재, allowlist 위반, 외부 전송 시도 등 |
| **PR_ONLY** | 치명 위반은 없으나 라인수·lockfile·테스트 등 사람 리뷰 필요. UNKNOWN 존재 시 AUTO_MERGE 금지. |
| **AUTO_MERGE** | G0~G6 전부 PASS, risk=LOW, allowlist 내 변경, REMOTE_GATE CONFIRMED(Stage 3 시) |

---

## 7. 화면(S1~S7)

| ID | 화면 | 목적 | Primary CTA |
|----|------|------|-------------|
| S1 | Queue Monitor | 큐 상태/STOP/요약 KPI | Claim Task |
| S2 | Task Detail | task/acceptance/risk/allowlist/commands 검증 | Open Plan |
| S3 | Plan | 범위/테스트/롤백/리스크 1장 고정 | Request Patch Draft |
| S4 | Patch Diff | OpenClaw 제안 diff 전용(읽기전용) | Run Gates |
| S5 | Gate Results | Gate PASS/FAIL + Evidence | Decide |
| S6 | PR & Merge | PR 생성/상태체크/Auto-merge 조건 | Create PR / Merge |
| S7 | Incident | ZERO_STOP/FAIL 로그·복구 | Recover / Rollback |

- 상세 UI 규칙: `config/uiux/SCREENS.md`, `config/uiux/UX_FLOW.md` 참조.

---

## 8. 정책 SSOT

| 구분 | 경로 | 용도 |
|------|------|------|
| Manifest | `MANIFEST.json` | 프로젝트명, stage, baton_file |
| Baton | `BATON_CURRENT.md` | 현재 Stage 요약 |
| 정책 | `config/policy/CURSOR_RULES.md` | 역할/권한/Queue/STOP/감사 요약 |
| | `config/policy/TOOL_POLICY.md` | 도구 사용 정책 |
| | `config/policy/APPROVAL_MATRIX.md` | 승인 매트릭스 |
| | `config/policy/AUDIT_LOG_SCHEMA.md` | 감사 로그 스키마 |
| Cursor 규칙 요약 | `.cursor/rules/AUTODEV_POLICY.md` | 자동개발 정책 요약 |

- 에이전트 실행 규칙 SSOT: **`AGENTS.md`** (README보다 우선).

---

## 9. 커맨드·스킬

### 9.1 커맨드(.cursor/commands/)

| 커맨드 | 용도 |
|--------|------|
| `/setup:init` | SSOT·Queue·Daily Audit DRY_RUN 점검, patch-only 제안 |
| `/queue:claim` | inbox→claimed 락, STOP·충돌 검사 |
| `/queue:open-plan` | S3 Plan 1장(PLAN.md, intent_lock.yml) |
| `/queue:request-patch-draft` | OpenClaw에 patch 제안 요청 |
| `/queue:run-gates` | G0~G6 실행, Evidence 수집 |
| `/queue:decide` | AUTO_MERGE / PR_ONLY / ZERO_STOP 결정 |
| `/queue:pr-merge` | PR 생성·상태체크·merge(조건/승인) |
| `/incident:recover` | Incident 복구 체크리스트·리포트 |

### 9.2 스킬(.cursor/skills/)

- **stop-check**: STOP 감지 → ZERO_STOP 수렴  
- **claim-lock**: inbox→claimed Claim/락, LOCK_CONFLICT 처리  
- **intake-validate**: 필수 파일·allowlist·보호구역 검증  
- **queue-scan**: 큐 상태 스캔  
- **patch-draft-request**: OpenClaw에 draft patch 요청  
- **patch-review**: diff 스캔(라인/삭제/lockfile/allowlist)  
- **diff-risk-scan**: diff 요약·risk_level  
- **gate-runner**: G1~G6 실행·evidence  
- **decision-router**: Gate/Risk/STOP → AUTO_MERGE/PR_ONLY/ZERO_STOP  
- **audit-append**: append-only 감사 로그 기록  
- **pr-merge-orchestrator**: PR 생성·merge 조건 정리  
- **incident-brief**: S7 Incident 리포트(원인/영향/복구)  

---

## 10. 감사·데이터

- **감사 로그**: append-only. 수정/삭제 금지.
- **저장 위치**(AGENTS.md 기준): `.autodev_queue/audit/<YYYY-MM-DD>/` — 작업별 `<TASK_ID>.jsonl`, 전역 `_global.jsonl`.
- **Stage 3 예시**: `.autodev_queue/audit/audit_log_YYYY-MM-DD.jsonl`, `.autodev_queue/audit/setup_init_report_YYYY-MM-DD.md` 등.
- **스키마**: `config/policy/AUDIT_LOG_SCHEMA.md`.

---

## 11. STOP(킬스위치)

- **조건**: `.autodev_queue/STOP` 존재(파일 또는 폴더).
- **행동**: 모든 실행 CTA 비활성, 진행 중 작업은 blocked 격리(이동 예약), S7 Incident에서만 복구·알림. STOP 해제 전 재시도 불가.

---

## 12. 참조

- **에이전트 규칙**: [AGENTS.md](../AGENTS.md)  
- **README**: [README.md](../README.md)  
- **로드맵**: [docs/ROADMAP.md](ROADMAP.md)  
- **화면 상세**: [config/uiux/SCREENS.md](../config/uiux/SCREENS.md)  
- **Gate 절차(Stage 3)**: [.cursor/commands/queue-run-gates.md](../.cursor/commands/queue-run-gates.md)
