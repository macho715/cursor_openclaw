---
id: skill.queue.block
name: queue.block
stage: 6.00
type: skill_spec
description: "안전 차단. blocked 상태로 수렴(언제든 호출 가능)"
model: fast
readonly: true
needs_approval: false
approval_owner: null
timeout_sec: 0
retry_max: 0
schemas:
  input:  docs/skills/schemas/skill.queue.block.input.schema.json
  output: docs/skills/schemas/skill.queue.block.output.schema.json
deny_conditions:
  - "없음(안전 조치이므로 언제든 허용)"
audit:
  event_name: "queue.block"
  event_schema: "docs/skills/schemas/audit.event.schema.json"
artifacts_out:
  - ".autodev_queue/<TASK_ID>/blocked/block.json (권장)"
---

# skill.queue.block(task_id, reason_code, reason_detail)

## 목적
- STOP/무결성 실패/승인 거절/게이트 실패 등에서 즉시 blocked로 수렴한다.

## 허용 사유코드
- STOP_DETECTED
- LOCK_CONFLICT
- INPUT_MISSING
- RUN_APPROVAL_DENIED
- EXEC_FAIL
- GATE_FAIL
- AUDIT_FAIL
- MANUAL_REVIEW_REQUIRED

## 후속(강제)
- blocked 이후에는 추가 실행 제안 금지
- 오직 수동 리뷰/인풋 보완/락 해제 같은 수동 단계만 안내
