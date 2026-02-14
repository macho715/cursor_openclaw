# /queue:decide
AUTO_MERGE/PR_ONLY/ZERO_STOP 결정

Status: active  
Timezone: Asia/Dubai  
Stage: 3.00 (Cursor Project Setting)  
Scope: 문서/설정 텍스트만 (구현/실행/배포 금지)  

---

## 0) 목적

- `/queue:run-gates` 결과를 입력으로 **Decision을 3종으로만 고정**한다:
  - `AUTO_MERGE`
  - `PR_ONLY`
  - `ZERO_STOP`
- UNKNOWN이 남아있으면 AUTO_MERGE로 승격하지 않는다(가정 금지).

---

## 1) 입력(Inputs)

| Item | Value |
|---|---|
| JOB_ID | `<JOB_ID>` |
| gate_results | `work/<JOB_ID>/gate_results.json` |
| GATES.md | `work/<JOB_ID>/GATES.md` |
| INPUT REQUIRED (브랜치/체크/allowlist_write) | UNKNOWN |

---

## 2) 결정 규칙(고정)

### 2.1 ZERO_STOP (STOP 우선)
아래 중 1.00개라도 충족 시 `ZERO_STOP`:
- G0_STOP = FAIL
- G4_ALLOWLIST = FAIL
- G5_SECRETS = FAIL
- G6_APPEND_ONLY = FAIL

### 2.2 AUTO_MERGE (저위험 자동머지)
아래 모두 PASS이고, REMOTE_GATE가 **PASS(CONFIRMED)** 일 때만:
- G0 PASS
- G1 PASS
- G2 PASS (≤300.00)
- G3 PASS (삭제/dep·lock/이진 0.00)
- G4 PASS
- G5 PASS
- G6 PASS
- REMOTE_GATE PASS
- INPUT REQUIRED 3개가 모두 CONFIRMED(UNKNOWN이면 금지)

### 2.3 PR_ONLY (기본)
ZERO_STOP가 아니고, AUTO_MERGE 조건을 만족하지 못하면 `PR_ONLY`.
- 특히 `REMOTE_GATE=UNKNOWN` 또는 INPUT REQUIRED가 UNKNOWN이면 PR_ONLY 고정.

---

## 3) 산출물(Outputs)

| Output | Path |
|---|---|
| DECISION | `work/<JOB_ID>/DECISION.md` |
| Audit Log | `.autodev_queue/audit/audit_log_YYYY-MM-DD.jsonl` |

---

## 4) DECISION.md 템플릿(고정)

```md
# DECISION — <JOB_ID>

Decision: PR_ONLY
Date: YYYY-MM-DD

## Gate Summary
- G0_STOP: PASS
- G1_DAILY_AUDIT: UNKNOWN
- G2_PATCH_SIZE: PASS (added=0.00, deleted=0.00, total=0.00)
- G3_FILE_SAFETY: PASS (del=0.00, dep_lock=0.00, bin=0.00)
- G4_ALLOWLIST: UNKNOWN
- G5_SECRETS: PASS
- G6_APPEND_ONLY: PASS
- REMOTE_GATE: UNKNOWN

## Why
- UNKNOWN 존재(REMOTE/INPUT REQUIRED 포함) → AUTO_MERGE 승격 금지

## Next
- /queue:pr-merge (PR_ONLY 경로)
```

---

## 5) 감사로그(append-only) 예시

```json
{
  "date": "YYYY-MM-DD",
  "actor": "Cursor",
  "queue_state_from": "work",
  "queue_state_to": "work",
  "decision": "PR_ONLY",
  "gate_results": {
    "G0_STOP": "PASS",
    "G1_DAILY_AUDIT": "UNKNOWN",
    "G2_PATCH_SIZE": "PASS",
    "G3_FILE_SAFETY": "PASS",
    "G4_ALLOWLIST": "UNKNOWN",
    "G5_SECRETS": "PASS",
    "G6_APPEND_ONLY": "PASS",
    "REMOTE_GATE": "UNKNOWN"
  },
  "evidence_refs": ["DECISION_CREATED"],
  "masked_notes": "job_id=<MASKED>"
}
```
