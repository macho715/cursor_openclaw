# /queue:pr-merge
PR 생성/상태체크/merge(조건/승인 기반)

Status: active  
Timezone: Asia/Dubai  
Stage: 3.00 (Cursor Project Setting)  
Scope: 문서/설정 텍스트만 (구현/실행/배포 금지)  

---

## 0) 목적

- Decision(`AUTO_MERGE/PR_ONLY/ZERO_STOP`)에 따라 PR 생성/체크/머지 절차를 고정한다.
- Protected branch / Required status checks는 **CONFIRMED/UNKNOWN**으로 분리한다.
- UNKNOWN이 남으면 AUTO_MERGE는 금지(=PR_ONLY 유지).

---

## 1) INPUT REQUIRED (없으면 UNKNOWN 유지)

| Item | Value |
|---|---|
| 기본 브랜치명 | UNKNOWN |
| Protected branch 사용 여부 | UNKNOWN |
| Required status checks 목록 | UNKNOWN |

---

## 2) 입력(Inputs)

| Item | Value |
|---|---|
| JOB_ID | `<JOB_ID>` |
| DECISION | `work/<JOB_ID>/DECISION.md` |
| Gate Results | `work/<JOB_ID>/GATES.md` |
| Patch(diff) | `<DIFF_REF>` |

---

## 3) Decision별 절차(고정)

### 3.1 ZERO_STOP
1. PR 생성 금지  
2. 작업 폴더 `blocked/` 격리  
3. 감사로그: 사유/위험/다음조치 기록  
4. 복구는 `/incident:recover`로만 진행

### 3.2 PR_ONLY (기본)
1. PR 생성(승인 기반)  
2. 상태체크 대기(Required checks가 UNKNOWN이면, “충족 판정”을 하지 않는다)  
3. 리뷰 승인(승인 주체는 APPROVAL_MATRIX에 따름)  
4. 모든 조건이 CONFIRMED일 때만 merge  

### 3.3 AUTO_MERGE (저위험)
AUTO_MERGE는 아래가 **CONFIRMED**일 때만 수행:
- Protected branch=CONFIRMED
- Required status checks 목록=CONFIRMED
- checks 상태가 PASS(허용 상태: successful/skipped/neutral)

CONFIRMED가 아니면 즉시 PR_ONLY로 강등한다.

---

## 4) 산출물(Outputs)

| Output | Path | Notes |
|---|---|---|
| PR 기록 | `pr/<JOB_ID>/PR.md` | 원문 링크 금지 |
| Merge 기록 | `done/<JOB_ID>/MERGE.md` | 원문 링크 금지 |
| Post-check | `done/<JOB_ID>/POSTCHECK.md` | 권장 |
| Audit Log | `.autodev_queue/audit/audit_log_YYYY-MM-DD.jsonl` | append-only |

---

## 5) PR.md 템플릿(고정)

```md
# PR — <JOB_ID>

Decision: PR_ONLY
Date: YYYY-MM-DD

## Branch
- base_branch: UNKNOWN

## Required Checks
- required_checks: UNKNOWN
- check_state: UNKNOWN

## Evidence Refs (원문 링크 금지)
- PR_REF: PR_<MASKED>
- CHECKS_REF: CI_<MASKED>
```

---

## 6) Merge 체크리스트(UNKNOWN 있으면 AUTO_MERGE 금지)

| Item | Required | Status |
|---|---:|---|
| STOP 없음 | YES | UNKNOWN |
| Gate G0~G6 PASS | YES | UNKNOWN |
| Required checks PASS | YES | UNKNOWN |
| allowlist 위반 0.00 | YES | UNKNOWN |
| 삭제/dep·lock/이진 0.00 | YES | UNKNOWN |
| 민감정보 원문 0.00 | YES | UNKNOWN |

---

## 7) done 산출물 템플릿(권장)

### 7.1 MERGE.md

```md
# MERGE — <JOB_ID>

Date: YYYY-MM-DD
Decision: AUTO_MERGE

## Outcome
- merged: true
- method: AUTO_MERGE / MANUAL_MERGE

## Evidence Refs (원문 링크 금지)
- PR_REF: PR_<MASKED>
- CHECKS_REF: CI_<MASKED>
- MERGE_REF: MERGE_<MASKED>
```

### 7.2 POSTCHECK.md

```md
# POSTCHECK — <JOB_ID>

Date: YYYY-MM-DD

## Checks
- gates_reconfirmed: PASS/FAIL/UNKNOWN
- audit_appended: PASS/FAIL
- artifacts_moved_to_done: PASS/FAIL
```

---

## 8) 감사로그(append-only) 예시

```json
{
  "date": "YYYY-MM-DD",
  "actor": "Cursor",
  "queue_state_from": "pr",
  "queue_state_to": "done",
  "decision": "PR_ONLY",
  "gate_results": {
    "G0_STOP": "PASS",
    "G1_DAILY_AUDIT": "PASS",
    "G2_PATCH_SIZE": "PASS",
    "G3_FILE_SAFETY": "PASS",
    "G4_ALLOWLIST": "PASS",
    "G5_SECRETS": "PASS",
    "G6_APPEND_ONLY": "PASS",
    "REMOTE_GATE": "UNKNOWN"
  },
  "evidence_refs": ["PR_MERGED"],
  "masked_notes": "job_id=<MASKED>; pr_ref=<MASKED>"
}
```
