---
id: skill.queue.decide
name: queue.decide
stage: 6.00
type: skill_spec
description: "gate/STOP/audit 결과로 PR_ONLY 또는 ZERO_STOP 결정"
model: inherit
readonly: true
needs_approval: false
approval_owner: null
timeout_sec: 0
retry_max: 0
schemas:
  input:  docs/skills/schemas/skill.queue.decide.input.schema.json
  output: docs/skills/schemas/skill.queue.decide.output.schema.json
deny_conditions:
  - "필수 입력 누락"
audit:
  event_name: "queue.decide"
  event_schema: "docs/skills/schemas/audit.event.schema.json"
artifacts_out:
  - "artifacts/<TASK_ID>/decision.json"
---

# skill.queue.decide(task_id, gate_status, stop_detected, audit_ok)

## 목적
- Stage6 분기 규칙을 결정문으로 고정한다.
- 결정은 PR_ONLY 또는 ZERO_STOP만 허용. AUTO_MERGE 금지.

## 규칙
- stop_detected=true 또는 audit_ok=false 또는 gate_status=fail → ZERO_STOP
- 그 외 → PR_ONLY
- auto_merge_forbidden은 반드시 true
