# AUDIT_LOG_SCHEMA (Policy SSOT) — Append-only Audit Log

Status: active  
Baton_ID: cursor_setting_policy_lock_v2.0  
Timezone: Asia/Dubai  
Updated: 2026-02-14  
Scope: 정책 문서/설정 텍스트만 (구현/실행/배포 금지)

---

## 1) 기본 원칙

1. 감사로그는 **append-only**다(기존 라인 수정/삭제 금지).
2. 모든 상태 전이와 Decision은 감사로그에 남는다.
3. 민감정보 원문은 금지하며 `<MASKED>`로 기록한다.

---

## 2) 권장 저장 위치(SSOT 연계)

| Item | Path |
|---|---|
| Audit Root | `.autodev_queue/audit/` |
| Daily Audit | `Daily_GoNoGo_YYYY-MM-DD.md` |
| Append-only Log | `audit_log_YYYY-MM-DD.jsonl` (권장) |

---

## 3) 필수 필드(Required)

### 3.1 공통 필드

| Field | Type | Required | Notes |
|---|---|---|---|
| date | string | YES | `YYYY-MM-DD` |
| actor | string | YES | `Cursor` / `OpenClaw` / `Operator` |
| queue_state_from | string | YES | inbox/claimed/work/pr/done/blocked |
| queue_state_to | string | YES | inbox/claimed/work/pr/done/blocked |
| decision | string | YES | AUTO_MERGE/PR_ONLY/ZERO_STOP |
| gate_results | object | YES | G0~G6 결과 |
| evidence_refs | array[string] | YES | 링크 원문 금지(식별자만) |
| masked_notes | string | YES | `<MASKED>` 적용 |

### 3.2 권장 필드(Recommended)

| Field | Type | Notes |
|---|---|---|
| baton_id | string | `cursor_setting_policy_lock_v2.0` |
| artifact_id | string | 작업 폴더/요청 식별자 |
| patch_id | string | diff 식별자(해시 등) |
| files_changed_count | number | 소수점 2.00자리로 기록 |
| lines_added | number | 소수점 2.00자리로 기록 |
| lines_deleted | number | 소수점 2.00자리로 기록 |
| is_binary_change | boolean | 기본 false |
| is_dep_lock_change | boolean | 기본 false |
| stop_present | boolean | STOP 감지 여부 |

---

## 4) Gate Results 객체(권장 구조)

`gate_results`는 아래 키를 포함한다(추가 가능):

| Key | Type | Meaning |
|---|---|---|
| G0_STOP | string | PASS/FAIL |
| G1_DAILY_AUDIT | string | PASS/FAIL/UNKNOWN |
| G2_PATCH_SIZE | string | PASS/FAIL |
| G3_FILE_SAFETY | string | PASS/FAIL |
| G4_ALLOWLIST | string | PASS/FAIL/UNKNOWN |
| G5_SECRETS | string | PASS/FAIL |
| G6_APPEND_ONLY | string | PASS/FAIL |
| REMOTE_GATE | string | PASS/FAIL/UNKNOWN |

---

## 5) STOP 발생 로그 규칙(필수)

STOP 발생 시 아래를 반드시 기록한다:

| Item | Required |
|---|---|
| stop_present=true | YES |
| decision=ZERO_STOP | YES |
| masked_notes에 사유/위험/다음조치 | YES |
| queue_state_to=blocked | YES |

---

## 6) 예시(형식 예시, 값은 예시)

> 아래는 스키마 형태 예시이며, 실제 키/값은 `<MASKED>` 정책을 따른다.

```json
{
  "date": "2026-02-14",
  "actor": "Cursor",
  "queue_state_from": "work",
  "queue_state_to": "pr",
  "decision": "PR_ONLY",
  "gate_results": {
    "G0_STOP": "PASS",
    "G1_DAILY_AUDIT": "PASS",
    "G2_PATCH_SIZE": "PASS",
    "G3_FILE_SAFETY": "PASS",
    "G4_ALLOWLIST": "UNKNOWN",
    "G5_SECRETS": "PASS",
    "G6_APPEND_ONLY": "PASS",
    "REMOTE_GATE": "UNKNOWN"
  },
  "evidence_refs": ["GH_PROTECTED_BRANCH_DOC", "OLLAMA_OPENAI_COMPAT_DOC"],
  "masked_notes": "base_branch=UNKNOWN; required_checks=UNKNOWN; paths=<MASKED>"
}
```
