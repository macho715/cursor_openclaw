---
id: skill.queue.work
name: queue.work
stage: 6.00
type: skill_spec
description: "task work 단계 전환 제안(패치/검증 준비 상태)"
model: inherit
readonly: true
needs_approval: false
approval_owner: null
timeout_sec: 0
retry_max: 0
schemas:
  input:  docs/skills/schemas/skill.queue.work.input.schema.json
  output: docs/skills/schemas/skill.queue.work.output.schema.json
deny_conditions:
  - "STOP_DETECTED"
  - "LOCK_CONFLICT"
  - "INPUT_MISSING"
  - "claimed 선행조건 불충족"
audit:
  event_name: "queue.work"
  event_schema: "docs/skills/schemas/audit.event.schema.json"
artifacts_out: []
---

# skill.queue.work(task_id)

## 목적
- claimed 이후 work 단계로 전환해 DRY_RUN 준비 상태를 만든다(제안).

## Deny (Hard)
- STOP/LOCK/INPUT_MISSING
- claimed가 아닌 것으로 판정되는 경우

## 복구
- 선행조건 불충족 시 queue.block(reason_code=MANUAL_REVIEW_REQUIRED) 권고
