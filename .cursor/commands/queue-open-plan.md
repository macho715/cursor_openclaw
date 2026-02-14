# /queue:open-plan
S3 Plan 1장 요약 생성(범위/테스트/롤백/리스크)

Status: active  
Timezone: Asia/Dubai  
Stage: 3.00 (Cursor Project Setting)  
Scope: 문서/설정 텍스트만 (구현/실행/배포 금지)  

---

## 0) 목적

- `claimed/<JOB_ID>` 작업에 대해 **1장짜리 PLAN**(스코프/가드/검증/복구)을 고정 포맷으로 만든다.
- PLAN은 OpenClaw patch 제안의 “입력 계약(SSOT)”이며, 이후 단계에서 **Intent Lock**으로 사용된다.

---

## 1) 입력(Inputs)

| Item | Value |
|---|---|
| JOB_ID | `<JOB_ID>` |
| Queue Path | `.autodev_queue/claimed/<JOB_ID>/` |
| 기본 브랜치명 | UNKNOWN |
| Required status checks | UNKNOWN |
| allowlist_write | UNKNOWN |

---

## 2) 산출 위치(권장)

| File | Path | Purpose |
|---|---|---|
| PLAN | `claimed/<JOB_ID>/PLAN.md` | 1장 계획 |
| INTENT LOCK | `claimed/<JOB_ID>/intent_lock.yml` | “바꾸지 않을 것” 잠금 |
| EVIDENCE | `claimed/<JOB_ID>/EVIDENCE.md` | 링크 원문 금지(식별자만) |

---

## 3) 작성 절차(DRY_RUN → 문서 작성)

1. STOP 존재 여부 확인(있으면 즉시 중단)  
2. 요청(REQUEST) 확인  
   - 요청 텍스트가 없으면, PLAN에 `request=UNKNOWN`으로 남긴다(가정 금지).  
3. Scope 정의  
   - allowlist_write가 UNKNOWN이면, Stage 3 범위(정책/커맨드 텍스트)로만 제한:
     - `docs/policy/**`
     - `.cursor/**`
4. Out-of-scope(금지) 고정  
   - 코드 구현/실행/배포 금지  
   - 파일 삭제 0.00, dep/lockfile 변경 0.00, 이진 변경 0.00  
   - 민감정보 원문 금지(`<MASKED>`)  
5. Validation(검증) 정의  
   - Gate(G0~G6) 결과표 생성(실행 지시 아님)  
6. Rollback/Recovery 정의  
   - 실패 시 blocked 격리 + audit 기록  
7. Evidence Refs 정리  
   - 원문 링크/내부 URL 금지, “식별자”만 기록  

---

## 4) PLAN.md 템플릿(고정)

```md
# PLAN — <JOB_ID>

## A) Request
- request: UNKNOWN

## B) Scope (허용 변경)
- allowlist_write: UNKNOWN
- allowed_paths:
  - docs/policy/**
  - .cursor/**

## C) Out of Scope (금지)
- code_implementation: true
- execution_or_deploy: true
- delete_files: 0.00
- dep_lock_changes: 0.00
- binary_changes: 0.00
- secrets_or_internal_urls_raw: 0.00

## D) Deliverables
- patch-only(유니파이드 diff)로 문서 생성/수정
- audit append-only 기록
- outputs:
  - claimed/<JOB_ID>/PLAN.md
  - claimed/<JOB_ID>/intent_lock.yml (권장)
  - work/<JOB_ID>/GATES.md (후속)

## E) Validation (예시, 실행 지시 아님)
- run_gates:
  - G0 STOP
  - G1 Daily Go/No-Go
  - G2 Patch size ≤ 300.00
  - G3 File safety(삭제/dep/lock/이진 0.00)
  - G4 Allowlist
  - G5 Secrets
  - G6 Append-only
- decision: AUTO_MERGE / PR_ONLY / ZERO_STOP

## F) Rollback / Recovery
- on_fail: decision=ZERO_STOP, move_to=blocked, audit=append
- resume: Operator 승인 필요

## G) Risks / Gates Focus
- STOP 우선
- allowlist_write UNKNOWN이면 AUTO_MERGE 금지
- secrets 1.00건이라도 즉시 ZERO_STOP

## H) Evidence Refs (원문 링크 금지)
- REQUEST_REF: <MASKED>
- POLICY_REF: CURSOR_RULES/TOOL_POLICY/APPROVAL_MATRIX/AUDIT_LOG_SCHEMA
```

---

## 5) intent_lock.yml 템플릿(권장)

```yml
job_id: "<JOB_ID>"
locked:
  - no_code_implementation
  - no_execution_or_deploy
  - no_delete_files
  - no_dep_lock_changes
  - no_binary_changes
  - no_secrets_or_internal_urls_raw
unknowns:
  - base_branch
  - required_status_checks
  - allowlist_write
```

---

## 6) EVIDENCE.md 규칙

- URL 원문 금지, 내부 URL/실경로 금지  
- 아래처럼 “키”만 기록:

```md
# EVIDENCE — <JOB_ID>

- REQUEST_REF: <MASKED>
- GH_PROTECTED_BRANCH_DOC
- OLLAMA_OPENAI_COMPAT_DOC
- DAILY_AUDIT_YYYY-MM-DD
```

---

## 7) 산출물(Outputs)

| Output | Path |
|---|---|
| PLAN | `.autodev_queue/claimed/<JOB_ID>/PLAN.md` |
| INTENT LOCK(권장) | `.autodev_queue/claimed/<JOB_ID>/intent_lock.yml` |
| EVIDENCE(권장) | `.autodev_queue/claimed/<JOB_ID>/EVIDENCE.md` |
