# /queue:run-gates
G0~G6 실행 + Evidence 수집

Status: active  
Timezone: Asia/Dubai  
Stage: 3.00 (Cursor Project Setting)  
Scope: 문서/설정 텍스트만 (구현/실행/배포 금지)  

---

## 0) 목적

- 제안된 diff(패치)를 **Gate(G0~G6)** 로 평가하여 `PASS/FAIL/UNKNOWN`을 산출한다.
- 결과는 `/queue:decide`의 입력이며, UNKNOWN이 남으면 AUTO_MERGE 승격을 금지한다.

---

## 1) 입력(Inputs)

| Item | Value |
|---|---|
| JOB_ID | `<JOB_ID>` |
| Patch(diff) | `<DIFF_REF>` |
| 오늘 Daily audit=Go | UNKNOWN |
| allowlist_write | UNKNOWN |
| Required status checks | UNKNOWN |

---

## 2) Gate 정의(고정)

| Gate | Name | PASS 조건 | FAIL 시 |
|---|---|---|---|
| G0 | STOP | STOP 미존재 | ZERO_STOP |
| G1 | Daily Go/No-Go | 오늘 audit=Go | AUTO_MERGE 금지(PR_ONLY) |
| G2 | Patch Size | added+deleted ≤ 300.00 | AUTO_MERGE 금지(PR_ONLY) |
| G3 | File Safety | 삭제 0.00 / dep·lock 0.00 / 이진 0.00 | PR_ONLY 또는 ZERO_STOP |
| G4 | Allowlist | allowlist_write 내부만 | ZERO_STOP |
| G5 | Secrets/NDA | 민감정보 원문 0.00 | ZERO_STOP |
| G6 | Append-only | 감사로그 append-only | ZERO_STOP |

REMOTE_GATE(별도 기록):
- Protected branch / Required checks 상태는 **CONFIRMED/UNKNOWN** 분리 기록
- UNKNOWN이면 AUTO_MERGE에서 PASS로 간주 금지

---

## 3) DRY_RUN 평가 절차(점검만)

1. G0 STOP: `.autodev_queue/STOP` 존재 여부  
2. G1 Daily audit:
   - 오늘자 audit 파일 존재/결과(Go/No-Go) 확인
   - 없으면 `UNKNOWN`
3. G2 Patch size:
   - diff에서 `+`/`-` 라인 수를 산출하여 2.00자리로 기록
4. G3 File safety:
   - 파일 삭제 여부
   - dep/lockfile 변경 여부
   - 이진 변경 여부(추정 금지: “탐지 기준”을 Evidence로 남김)
5. G4 Allowlist:
   - allowlist_write가 UNKNOWN이면 허용 경로를 Stage 3 텍스트 범위로 제한:
     - `docs/policy/**`
     - `.cursor/**`
6. G5 Secrets:
   - 토큰/키/내부 URL/실경로 원문 탐지 시 FAIL
7. G6 Append-only:
   - audit log 파일에 “기존 라인 수정/삭제” 흔적이 있는지 확인(원본 보존)
8. REMOTE_GATE:
   - 설정이 확인되지 않으면 `UNKNOWN`

---

## 4) 산출물(Outputs)

| Output | Path | Notes |
|---|---|---|
| Gate 결과표 | `work/<JOB_ID>/GATES.md` | 표 1개로 고정 |
| Gate 결과 JSON | `work/<JOB_ID>/gate_results.json` | 권장 |
| Evidence | `work/<JOB_ID>/EVIDENCE.md` | 원문 링크 금지 |
| Audit Log | `.autodev_queue/audit/audit_log_YYYY-MM-DD.jsonl` | append-only |

---

## 5) GATES.md 포맷(고정)

```md
# GATES — <JOB_ID>

| Gate | Result | Metric/Note |
|---|---|---|
| G0_STOP | PASS/FAIL | stop_present=false |
| G1_DAILY_AUDIT | PASS/FAIL/UNKNOWN | daily=Go? |
| G2_PATCH_SIZE | PASS/FAIL | added=0.00, deleted=0.00, total=0.00 |
| G3_FILE_SAFETY | PASS/FAIL | del=0.00, dep_lock=0.00, bin=0.00 |
| G4_ALLOWLIST | PASS/FAIL/UNKNOWN | allowlist_write=UNKNOWN |
| G5_SECRETS | PASS/FAIL | secrets_raw=0.00 |
| G6_APPEND_ONLY | PASS/FAIL | append_only=true |
| REMOTE_GATE | PASS/FAIL/UNKNOWN | protected=UNKNOWN, checks=UNKNOWN |
```

---

## 6) gate_results.json(권장 구조)

```json
{
  "job_id": "<JOB_ID>",
  "date": "YYYY-MM-DD",
  "metrics": {
    "lines_added": 0.00,
    "lines_deleted": 0.00,
    "lines_total": 0.00,
    "files_deleted": 0.00,
    "dep_lock_changes": 0.00,
    "binary_changes": 0.00,
    "secrets_raw": 0.00
  },
  "gates": {
    "G0_STOP": "PASS",
    "G1_DAILY_AUDIT": "UNKNOWN",
    "G2_PATCH_SIZE": "PASS",
    "G3_FILE_SAFETY": "PASS",
    "G4_ALLOWLIST": "UNKNOWN",
    "G5_SECRETS": "PASS",
    "G6_APPEND_ONLY": "PASS",
    "REMOTE_GATE": "UNKNOWN"
  }
}
```

---

## 7) Evidence 규칙(원문 링크 금지)

EVIDENCE.md에는 “키”만 기록한다:

```md
# EVIDENCE — <JOB_ID>

- DIFF_REF: DIFF_<MASKED>
- DAILY_AUDIT: DAILY_AUDIT_YYYY-MM-DD
- POLICY: CURSOR_RULES / TOOL_POLICY / APPROVAL_MATRIX / AUDIT_LOG_SCHEMA
- REMOTE_GATE_STATUS: UNKNOWN
```

---

## 8) No-Go 우선순위

| Condition | Decision |
|---|---|
| G0/G4/G5/G6 중 1.00개라도 FAIL | ZERO_STOP |
| 그 외 FAIL 또는 UNKNOWN 존재 | PR_ONLY |
| ALL PASS + REMOTE_GATE PASS(CONFIRMED) | AUTO_MERGE 후보 |
