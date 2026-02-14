---
id: skill.audit.verify
name: audit.verify
stage: 6.00
type: skill_spec
description: "append-only 감사로그 체인 무결성 검증"
model: fast
readonly: true
needs_approval: false
approval_owner: null
timeout_sec: 0
retry_max: 0
schemas:
  input:  docs/skills/schemas/skill.audit.verify.input.schema.json
  output: docs/skills/schemas/skill.audit.verify.output.schema.json
deny_conditions: []
audit:
  event_name: "audit.verify"
  event_schema: "docs/skills/schemas/audit.event.schema.json"
artifacts_out:
  - "artifacts/<TASK_ID>/audit_verification.json"
---

# skill.audit.verify(task_id)

## 목적
- append-only 감사로그가 수정/삭제 없이 연결되었는지 검증한다.
- auto_merge_seen=true이면 즉시 ZERO_STOP 권고.

## 실패 처리
- audit_ok=false 또는 auto_merge_seen=true 시 queue.block(reason_code=AUDIT_FAIL)
