# /incident:recover
Incident 복구 체크리스트 생성

Status: active  
Timezone: Asia/Dubai  
Stage: 3.00 (Cursor Project Setting)  
Scope: 문서/설정 텍스트만 (구현/실행/배포 금지)  

---

## 0) 목적

- STOP/게이트 실패/충돌/감사로그 위반 등 Incident 발생 시,
  **확산 차단(Containment) → 원인 추적 → 복구(Recovery) → 재개 조건(Resume)** 을 1장 체크리스트로 고정한다.
- 외부 전송(WebChat/메일/업로드)은 기본 차단. 예외는 Operator 승인 + 텍스트-only + `<MASKED>`만 허용.

---

## 1) Incident 유형(분류)

| Type | Trigger | Default Decision |
|---|---|---|
| STOP | `.autodev_queue/STOP` 존재 | ZERO_STOP |
| ALLOWLIST | 허용 경로 밖 변경 | ZERO_STOP |
| SECRETS | 토큰/키/내부 URL/실경로 원문 | ZERO_STOP |
| AUDIT | append-only 위반 의심 | ZERO_STOP |
| CONFLICT | JOB_ID 중복 claim/work | PR_ONLY(조사) |
| GATE_FAIL | G1/G2/G3 FAIL | PR_ONLY 또는 ZERO_STOP |

---

## 2) 즉시 조치(Containment) — 우선순위

1. STOP 확인(존재 시 즉시 중단)  
2. 영향 JOB 식별(affected JOB_ID 목록화)  
3. 작업 격리: `blocked/`로 이동(절차에 따라)  
4. 증빙 보존: diff/gates/decision/audit log 원본을 수정하지 않는다  
5. 민감정보 노출 의심 시: “사본 보고서”에만 `<MASKED>` 반영(원본 변경 금지)

---

## 3) 복구 절차(Recovery)

### 3.1 사건 요약(필수)

| Field | Value |
|---|---|
| Incident_ID | `INC_YYYY-MM-DD_<MASKED>` |
| Date | `YYYY-MM-DD` |
| Type | STOP/ALLOWLIST/SECRETS/AUDIT/CONFLICT/GATE_FAIL |
| Affected JOB_ID | `<JOB_ID list>` |
| Current Queue State | inbox/claimed/work/pr/done/blocked |
| Decision | ZERO_STOP / PR_ONLY |

### 3.2 원인 추적(Policy 기반)
- Gate 결과(G0~G6)에서 FAIL/UNKNOWN 구간 확인
- DECISION.md와 실제 행동(상태 전이/PR/merge) 불일치 여부 확인
- audit log append-only 위반 여부 확인(원본 보존)

### 3.3 복구 액션(케이스별)

| Case | Action | Resume Rule |
|---|---|---|
| STOP | Operator 승인으로 STOP 해제 후 재개 | STOP 해제 + 기록 필수 |
| ALLOWLIST | 위반 변경 폐기 + PLAN 스코프 축소 | allowlist 100.00% 준수 |
| SECRETS | 노출 범위 최소화 + `<MASKED>` 보고서 | secrets_raw=0.00 |
| AUDIT | 원본 보존 + 새 로그 파일로 이어쓰기 | append-only 회복 |
| CONFLICT | 단일 claimant만 유지, 나머지 격리 | 중복 0.00 |

---

## 4) 산출물(Outputs)

| Output | Path | Notes |
|---|---|---|
| Incident Report | `.autodev_queue/audit/incident_report_YYYY-MM-DD_<MASKED>.md` | 텍스트-only |
| Recovery Checklist | `.autodev_queue/audit/incident_recover_YYYY-MM-DD_<MASKED>.md` | 1장 |
| Audit Log | `.autodev_queue/audit/audit_log_YYYY-MM-DD.jsonl` | append-only |

---

## 5) Incident Report 템플릿(고정)

```md
# INCIDENT REPORT — INC_YYYY-MM-DD_<MASKED>

## A) Summary
- Date: YYYY-MM-DD
- Type: STOP / ALLOWLIST / SECRETS / AUDIT / CONFLICT / GATE_FAIL
- Affected: <JOB_ID list>
- Decision: ZERO_STOP

## B) What Happened
- Trigger:
- First Detection:
- Scope:

## C) Gates Snapshot
- G0_STOP:
- G1_DAILY_AUDIT:
- G2_PATCH_SIZE:
- G3_FILE_SAFETY:
- G4_ALLOWLIST:
- G5_SECRETS:
- G6_APPEND_ONLY:
- REMOTE_GATE:

## D) Containment
- blocked isolation:
- evidence preserved:

## E) Recovery Plan
- next steps:
- owner: Operator/Cursor
- criteria to resume:

## F) Prevention
- policy changes:
- additional checks:

## Evidence Refs (원문 링크 금지)
- <EVIDENCE_KEY list>
```

---

## 6) 재개 조건(Resume Criteria)

다음이 모두 충족되어야 `blocked→inbox` 재개 가능:

| Item | Required |
|---|---:|
| STOP 해제(존재 시) | YES |
| allowlist 위반 0.00 | YES |
| secrets_raw 0.00 | YES |
| audit append-only 정상 | YES |
| PLAN/DECISION 재작성 | YES |

UNKNOWN이 1.00개라도 남으면 PR_ONLY로만 재개한다.
