# APPROVAL_MATRIX (Policy SSOT) — Decision / Gate / Approval

Status: active  
Baton_ID: cursor_setting_policy_lock_v2.0  
Timezone: Asia/Dubai  
Updated: 2026-02-14  
Scope: 정책 문서/설정 텍스트만 (구현/실행/배포 금지)

---

## 0) INPUT REQUIRED (없으면 UNKNOWN)

| Item | Value |
|---|---|
| 기본 브랜치명 | UNKNOWN |
| Required status checks 목록 | UNKNOWN |
| allowlist_write 경로 | UNKNOWN |

---

## 1) Decision 정의

| Decision | Meaning |
|---|---|
| AUTO_MERGE | 게이트 PASS 시 자동 머지(저위험) |
| PR_ONLY | PR 생성/리뷰로만 진행 |
| ZERO_STOP | 즉시 중단 + blocked 격리 |

---

## 2) 정량 Gate(저위험 자동머지 조건)

| Item | Threshold |
|---|---|
| 라인(추가+삭제) | ≤ 300.00 |
| dep/lockfile 변경 | 0.00 |
| 파일 삭제 | 0.00 |
| 이진 변경 | 0.00 |
| allowlist_write 외 변경 | 0.00 |
| STOP 존재 | 0.00 |
| 오늘 audit=Go | 1.00 (필수) |

---

## 3) Approval Matrix

| Decision | Gate 조건(요약) | 승인 주체 | 산출물(필수) | 롤백/재시도 |
|---|---|---|---|---|
| AUTO_MERGE | G0~G6 ALL PASS + Remote Gate CONFIRMED+PASS | Cursor(자동) + Operator(사전 승인: UNKNOWN) | merge 기록 + 감사로그 | 실패 시 revert + blocked 전환 |
| PR_ONLY | G0 PASS + G4 PASS + G5 PASS, 그 외 1.00개 이상 PASS 아님/UNKNOWN | Operator + CODEOWNERS(UNKNOWN) | PR + 체크리스트 + 감사로그 | Gate 보완 후 PR 업데이트 또는 재시도 |
| ZERO_STOP | No-Go 1.00개라도 충족 | Operator | blocked 격리 + STOP/사유 로그 | STOP 해제/입력 보완 후 inbox로 재개 |

---

## 4) Rollback / Recovery 경로(고정)

### 4.1 AUTO_MERGE 실패
- 실패 원인을 감사로그에 기록하고 `blocked/`로 격리
- 롤백은 "이전 상태 복원"을 목표로 하며, 증빙(메트릭/결정/사유)을 남긴다

### 4.2 PR_ONLY 실패(리뷰 반려/체크 실패)
- PR은 유지하되, Gate 재평가 후 수정 패치만 추가한다
- 스코프 확장/정책 예외는 Operator 승인 없이는 금지

### 4.3 ZERO_STOP 복구
- STOP 해제는 Operator만 가능
- 해제 후 `blocked → inbox` 전환은 감사로그 REQUIRED

---

## 5) Unknown 처리 규칙

- INPUT REQUIRED가 UNKNOWN이면, AUTO_MERGE 조건을 충족하더라도 Remote Gate를 PASS로 간주하지 않는다.
- Remote Gate가 UNKNOWN인 동안 Decision 기본값은 `PR_ONLY`이다(상위 Gate 위반 시 `ZERO_STOP`).
