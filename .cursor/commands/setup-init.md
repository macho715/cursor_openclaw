# /setup:init
SSOT 로드 + 큐 템플릿 DRY_RUN/적용 가이드

Status: active  
Timezone: Asia/Dubai  
Stage: 3.00 (Cursor Project Setting)  
Scope: 문서/설정 텍스트만 (구현/실행/배포 금지)  

---

## 0) 목적

- Stage 3(정책/레일)에서 **SSOT + Folder Queue + Daily Audit**가 “작동 가능한 최소 구성”인지 DRY_RUN으로 점검한다.
- 누락이 있으면 **patch-only(유니파이드 diff)** 로 “생성/보완안”만 제안한다(자동 적용 금지).
- STOP(킬스위치) 우선, 민감정보 `<MASKED>` 우선, INPUT REQUIRED 미입력은 **UNKNOWN 유지**가 원칙이다.

---

## 1) INPUT REQUIRED (없으면 UNKNOWN 유지, 가정 금지)

| Item | Value |
|---|---|
| 기본 브랜치명(main/master 등) | UNKNOWN |
| Required status checks 목록 | UNKNOWN |
| allowlist_write 경로 | UNKNOWN |

---

## 2) SSOT(기준 경로)

| Category | SSOT Path |
|---|---|
| Manifest | `MANIFEST.json` |
| Baton | `BATON_CURRENT.md` |
| Queue Root | `.autodev_queue/` |
| Daily Ops Template | `.autodev_queue/audit/Daily_GoNoGo_TEMPLATE.md` |
| Policy SSOT | `docs/policy/CURSOR_RULES.md` / `docs/policy/TOOL_POLICY.md` / `docs/policy/APPROVAL_MATRIX.md` / `docs/policy/AUDIT_LOG_SCHEMA.md` |
| Cursor Rule Summary | `.cursor/rules/AUTODEV_POLICY.md` |

---

## 3) DRY_RUN 체크리스트(점검만)

### 3.1 STOP 우선

| Check | PASS | FAIL |
|---|---|---|
| STOP 존재 여부 | `.autodev_queue/STOP` 미존재 | 즉시 `ZERO_STOP` + 진행 중단 |

### 3.2 Queue 구조 존재(폴더)

아래 폴더 “존재 여부만” 점검한다(빈 폴더는 `.gitkeep` 제안 가능):

| Folder | Required |
|---|---:|
| `.autodev_queue/inbox/` | YES |
| `.autodev_queue/claimed/` | YES |
| `.autodev_queue/work/` | YES |
| `.autodev_queue/pr/` | YES |
| `.autodev_queue/done/` | YES |
| `.autodev_queue/blocked/` | YES |
| `.autodev_queue/audit/` | YES |

### 3.3 Daily Go/No-Go 템플릿

| Check | PASS | FAIL |
|---|---|---|
| Template 존재 | `Daily_GoNoGo_TEMPLATE.md` 존재 | AUTO_MERGE 불가(최소 PR_ONLY) |

### 3.4 정책 문서 존재

| Policy | Required |
|---|---:|
| CURSOR_RULES | YES |
| TOOL_POLICY | YES |
| APPROVAL_MATRIX | YES |
| AUDIT_LOG_SCHEMA | YES |
| AUTODEV_POLICY (Cursor rules summary) | YES |

### 3.5 민감정보/경로 정책 점검(텍스트-only)

- 토큰/키/내부 URL/실경로 원문은 어떤 문서에도 남기지 않는다 → 발견 시 `<MASKED>` 처리.
- INPUT REQUIRED 3개(브랜치/체크/allowlist_write)가 UNKNOWN이면 **UNKNOWN 유지**(가정 금지).

---

## 4) APPLY_REQUEST(패치 제안만)

DRY_RUN 결과 누락이 있으면 다음만 수행한다:

1. 누락 항목을 목록화한다(보고서).
2. **patch-only** 로만 보완안을 제안한다.
3. 실제 apply/test/commit/merge는 Cursor(Control-Plane)가 **별도 승인 후** 수행한다.

---

## 5) 산출물(Outputs)

| Output | Path | Type |
|---|---|---|
| Setup DRY_RUN Report | `.autodev_queue/audit/setup_init_report_YYYY-MM-DD.md` | 텍스트 |
| Audit Log(권장) | `.autodev_queue/audit/audit_log_YYYY-MM-DD.jsonl` | JSONL(append-only) |

---

## 6) 보고서 템플릿(권장)

```md
# SETUP_INIT_REPORT — YYYY-MM-DD

## A) INPUT REQUIRED
- base_branch: UNKNOWN
- required_status_checks: UNKNOWN
- allowlist_write: UNKNOWN

## B) STOP
- stop_present: false

## C) Queue Folders
- inbox/claimed/work/pr/done/blocked/audit: PASS/FAIL

## D) Policy SSOT
- docs/policy/*: PASS/FAIL
- .cursor/rules/AUTODEV_POLICY.md: PASS/FAIL

## E) Decision Hint
- if any FAIL in STOP/allowlist/secrets: ZERO_STOP
- else: PR_ONLY (UNKNOWN inputs keep UNKNOWN)
```

---

## 7) 감사로그(append-only) 예시

```json
{
  "date": "YYYY-MM-DD",
  "actor": "Cursor",
  "queue_state_from": "inbox",
  "queue_state_to": "inbox",
  "decision": "PR_ONLY",
  "gate_results": {
    "G0_STOP": "PASS",
    "G4_ALLOWLIST": "UNKNOWN",
    "G5_SECRETS": "PASS",
    "REMOTE_GATE": "UNKNOWN"
  },
  "evidence_refs": ["SETUP_INIT_DRY_RUN"],
  "masked_notes": "base_branch=UNKNOWN; required_checks=UNKNOWN; allowlist_write=UNKNOWN"
}
```

---

## 8) ZERO_STOP 트리거(즉시 중단)

| Trigger | Reason |
|---|---|
| STOP 존재 | 킬스위치 우선 |
| allowlist 위반 감지 | 스코프 오염 |
| 민감정보 원문 감지 | 보안/NDA 위반 |
