# /queue:claim
inbox→claimed (락/충돌/STOP 체크)

Status: active  
Timezone: Asia/Dubai  
Stage: 3.00 (Cursor Project Setting)  
Scope: 문서/설정 텍스트만 (구현/실행/배포 금지)  

---

## 0) 목적

- `.autodev_queue/inbox/<JOB_ID>/` 작업을 **단일 작업자(Cursor)** 가 점유(Claim)한다.
- 중복/충돌/STOP 존재를 먼저 검사하고, 위반 시 **STOP 우선**으로 차단한다.

---

## 1) 입력(Inputs)

| Item | Value |
|---|---|
| JOB_ID | `<JOB_ID>` |
| From | `.autodev_queue/inbox/<JOB_ID>/` |
| To | `.autodev_queue/claimed/<JOB_ID>/` |
| Actor | `Cursor` (고정) |

---

## 2) DRY_RUN(점검만) — Claim 가능 판정

### 2.1 STOP

| Check | PASS | FAIL |
|---|---|---|
| STOP 존재 여부 | STOP 미존재 | 즉시 `ZERO_STOP` |

### 2.2 존재/중복 검사(상태 폴더 전수)

| Location | Expectation |
|---|---|
| inbox/<JOB_ID> | 존재(YES) |
| claimed/<JOB_ID> | 미존재(0.00) |
| work/<JOB_ID> | 미존재(0.00) |
| pr/<JOB_ID> | 미존재(0.00) |
| done/<JOB_ID> | 미존재(0.00) |
| blocked/<JOB_ID> | 미존재(0.00) *(존재 시 Operator 승인 필요)* |

판정:
- inbox에 없으면: `PR_ONLY`(요청 재확인)
- claimed/work/pr에 이미 있으면: `PR_ONLY`(충돌 조사)
- blocked에 있으면: 기본 `ZERO_STOP`(사유/위험 확인 후 Operator 재개)
- done에 있으면: 재사용 금지(새 JOB_ID로 재등록)

---

## 3) APPLY_REQUEST(상태 전이) — Cursor 소유

> 본 문서는 “절차 정의”다. 실제 이동/적용은 승인 후 Cursor가 수행한다.

1. `inbox/<JOB_ID>` → `claimed/<JOB_ID>` 로 이동(원자적 이동 우선)  
2. `claimed/<JOB_ID>/CLAIM.json` 생성(락)  
3. 감사로그 append-only 기록  

### 3.1 CLAIM.json 템플릿(민감정보 금지)

```json
{
  "job_id": "<JOB_ID>",
  "claimed_on": "YYYY-MM-DD",
  "actor": "Cursor",
  "notes": "<MASKED>"
}
```

---

## 4) 충돌 처리(필수 규칙)

### 4.1 “스테일 claim” 의심 기준(예시)

> 시간 기준은 환경마다 다르므로 숫자 가정 금지. 아래는 절차만 정의한다.

- claimed 폴더에 있으나:
  - work/pr로 진행 흔적 없음
  - audit log에 다음 단계 기록 없음

조치:

### 4.2 blocked 발견
- STOP 또는 ZERO_STOP 이력 가능성이 높으므로:
  - Operator 승인 없이는 재개 금지
  - incident report 먼저 작성(텍스트-only)

---

## 5) 산출물(Outputs)

| Output | Path |
|---|---|
| Claimed Folder | `.autodev_queue/claimed/<JOB_ID>/` |
| Claim Lock | `claimed/<JOB_ID>/CLAIM.json` |
| Audit Log | `.autodev_queue/audit/audit_log_YYYY-MM-DD.jsonl` |

---

## 6) 감사로그(append-only) 예시

```json
{
  "date": "YYYY-MM-DD",
  "actor": "Cursor",
  "queue_state_from": "inbox",
  "queue_state_to": "claimed",
  "decision": "PR_ONLY",
  "gate_results": {
    "G0_STOP": "PASS",
    "G6_APPEND_ONLY": "PASS"
  },
  "evidence_refs": ["QUEUE_CLAIM"],
  "masked_notes": "job_id=<MASKED>"
}
```

---

## 7) ZERO_STOP 트리거

| Trigger | Action |
|---|---|
| STOP 존재 | 즉시 중단 + blocked 격리(필요 시) |
| 중복 claim 확정(동시 수정 위험) | PR_ONLY로 강등 + incident 조사 |
| audit append-only 위반 의심 | 즉시 ZERO_STOP + 원본 보존 |
