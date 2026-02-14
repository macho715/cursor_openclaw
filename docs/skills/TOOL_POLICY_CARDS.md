# TOOL_POLICY_CARDS — Tool Classifications & Guards (Approval-by-default)

## 공통 원칙(불변)
- needsApproval 기본값: **true** (Read/Write/External/Costly 모두)
- External IO(업로드/메신저/웹전송): **기본 DENY**
- OpenClaw는 "제안만": EXEC/PR/MERGE/External IO 금지
- Allowlist 밖 경로 접근/수정 시도 → 즉시 ZERO_STOP
- Delete/파괴 명령 시도 → 즉시 ZERO_STOP
- Denied는 **재시도 금지**

---

## TOOL_CLASS: READ
- 예: 파일/디렉토리 목록, 내용 읽기, diff 읽기
- needsApproval: true
- DENY 조건:
  - Protected Zones 접근
  - Allowlist 밖 경로
- Audit fields(최소):
  - actor, tool_class=READ, paths[], result, event_id

## TOOL_CLASS: WRITE
- 예: draft patch/rationale 저장, 보고서/로그 작성
- needsApproval: true
- 허용 경로(원칙):
  - .autodev_queue/work/<TASK_ID>/** (제안 아티팩트)
  - .autodev_queue/audit/** (append-only)
  - .autodev_queue/blocked/<TASK_ID>/** (incident 산출물)
- DENY 조건:
  - 기존 파일 "수정(덮어쓰기)" (append-only 위반)
  - Protected Zones
  - Allowlist 밖
- Audit fields:
  - actor, tool_class=WRITE, path, append_only(true/false), event_id

## TOOL_CLASS: MOVE
- 예: inbox→claimed→work→pr→done/blocked 상태 전이(폴더 이동/rename)
- needsApproval: true
- DENY 조건:
  - 상태 전이 규칙 위반
  - 대상 task에 락/충돌 존재(LOCK_CONFLICT)
- Audit fields:
  - from_state, to_state, task_id, lock_path, event_id

## TOOL_CLASS: EXEC
- 예: 테스트/린트/게이트 실행
- needsApproval: true
- Cursor only: true
- timeout: 900s(권장) / retry: 0(기본)
- DENY 조건:
  - OpenClaw 실행
  - 네트워크/외부 전송 포함 커맨드
- Audit fields:
  - command_fingerprint, exit_code, evidence_paths[], event_id

## TOOL_CLASS: PR / MERGE
- needsApproval: true
- Cursor only: true
- DENY 조건:
  - OpenClaw 실행
  - Gate fail / risk=HIGH+핵심게이트 FAIL / STOP 감지
- Audit fields:
  - pr_url, checks_status, merge_status, event_id

## TOOL_CLASS: EXTERNAL
- 기본: DENY(차단)
- 예외 허용은 Stage 5 SSOT에 "명시"된 경우만(없으면 항상 DENY)

## TOOL_CLASS: COSTLY
- 예: 장시간 리서치/대규모 스캔
- needsApproval: true
- retry: 0(기본)
- Audit fields:
  - duration_ms, scope_hint, event_id
