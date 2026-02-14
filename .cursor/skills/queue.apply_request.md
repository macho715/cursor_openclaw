---
id: skill.queue.apply_request
name: queue.apply_request
stage: 6.00
type: skill_spec
description: "apply 실행 금지. 승인 요청 패키지(apply_request.json)만 생성"
model: inherit
readonly: true
needs_approval: false
approval_owner: null
timeout_sec: 0
retry_max: 0
schemas:
  input:  docs/skills/schemas/skill.queue.apply_request.input.schema.json
  output: docs/skills/schemas/skill.queue.apply_request.output.schema.json
preconditions:
  - "decision == PR_ONLY"
deny_conditions:
  - "decision != PR_ONLY"
  - "patch_refs 누락/비어있음(스키마가 차단)"
audit:
  event_name: "queue.apply_request"
  event_schema: "docs/skills/schemas/audit.event.schema.json"
artifacts_out:
  - ".autodev_queue/<TASK_ID>/approval/apply_request.json"
---

# skill.queue.apply_request(task_id, decision, patch_refs)

## 목적
- 실제 APPLY를 절대 수행하지 않고, 승인 요청 패키지만 만든다.
- 승인 owner는 Cursor 고정.

## Hard Rules
- decision이 PR_ONLY일 때만 허용
- AUTO_MERGE 경로/표기는 금지
- apply는 Stage6 범위 밖(명시적으로 금지)
