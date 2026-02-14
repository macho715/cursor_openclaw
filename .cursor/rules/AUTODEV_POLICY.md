# AUTODEV_POLICY (Cursor Rules Summary) — Folder Queue / Option A

Status: active  
Baton_ID: cursor_setting_policy_lock_v2.0  
Timezone: Asia/Dubai  
Updated: 2026-02-14  
Scope: 텍스트 규칙(코드 아님)

---

## 1) 권한 경계(불변)
- OpenClaw: diff/patch **제안만**
- Cursor: APPLY/TEST/COMMIT/PR/MERGE/ROLLBACK **소유**

---

## 2) 고정 플로우(불변)
**DRY_RUN → Diff → Gate → Decision(AUTO_MERGE/PR_ONLY/ZERO_STOP) → APPLY_REQUEST**

---

## 3) STOP(킬스위치)
- `.autodev_queue/STOP` 존재 시 즉시 **ZERO_STOP**
- 작업은 `blocked/` 격리 + 감사로그 append

---

## 4) AUTO_MERGE(저위험) 조건(요약)
- 라인(추가+삭제) ≤ **300.00**
- dep/lockfile 변경 **0.00**
- 파일 삭제 **0.00**, 이진 변경 **0.00**
- allowlist_write 외 변경 **0.00**
- 오늘 audit=Go
- Remote Gate(Protected branch/Required checks) = CONFIRMED+PASS
- INPUT REQUIRED 미제공 시 값은 **UNKNOWN** 유지

---

## 5) 보안/마스킹
- 토큰/키/내부 URL/실경로는 항상 `<MASKED>`
- 외부 전송 기본 차단(예외는 Operator 승인 + 텍스트-only + `<MASKED>`)

---

## 6) 출력 포맷(에이전트 응답)
1) 요약(5줄 이내)
2) 승인(Go/Revise)
3) patch-only(유니파이드 diff)
4) 검증/로그(PASS/WARN/FAIL + 변경 요약 3줄)
