---
id: skill.queue.dry_run
name: queue.dry_run
stage: 6.00
type: skill_spec
description: "DRY_RUN 실행 요청(승인 필요, Cursor만 실행 가능)"
model: inherit
readonly: true
needs_approval: true
approval_owner: "Cursor"
timeout_sec: 60
retry_max: 1
schemas:
  input:  docs/skills/schemas/skill.queue.dry_run.input.schema.json
  output: docs/skills/schemas/skill.queue.dry_run.output.schema.json
preconditions:
  - "state == work (권고)"
  - "run_approved.json 존재"
deny_conditions:
  - "run_approved.json 부재"
  - "STOP_DETECTED"
  - "LOCK_CONFLICT"
  - "INPUT_MISSING"
audit:
  event_name: "queue.dry_run"
  event_schema: "docs/skills/schemas/audit.event.schema.json"
artifacts_out:
  - "artifacts/<TASK_ID>/dry_run.json"
---

# skill.queue.dry_run(task_id)

## 목적
- 실제 변경 없이 DRY_RUN을 수행하고 evidence(dry_run.json)를 남긴다.
- 승인 전 실행 금지(run_approved 신호 필요).

## 승인(필수)
- `.autodev_queue/<TASK_ID>/approval/run_approved.json`

## 복구
- denied → `queue.block(reason_code="RUN_APPROVAL_DENIED")`
- fail → 재시도 1회 후 `queue.block(reason_code="EXEC_FAIL")`
