---
id: skill.queue.gate
name: queue.gate
stage: 6.00
type: skill_spec
description: "Gate 실행 요청(승인 필요, dry_run+diff 선행 필수)"
model: inherit
readonly: true
needs_approval: true
approval_owner: "Cursor"
timeout_sec: 90
retry_max: 1
schemas:
  input:  docs/skills/schemas/skill.queue.gate.input.schema.json
  output: docs/skills/schemas/skill.queue.gate.output.schema.json
preconditions:
  - "run_approved.json 존재"
  - "dry_run.status == ok"
  - "diff.status == ok"
deny_conditions:
  - "run_approved.json 부재"
  - "dry_run/diff 산출물 누락"
  - "STOP_DETECTED"
  - "LOCK_CONFLICT"
  - "INPUT_MISSING"
audit:
  event_name: "queue.gate"
  event_schema: "docs/skills/schemas/audit.event.schema.json"
artifacts_out:
  - "artifacts/<TASK_ID>/gate.json"
---

# skill.queue.gate(task_id)

## 목적
- Gate를 실행하고 gate.json evidence를 생성한다.
- gate_status는 pass/fail로 산출된다.

## 선행조건(Hard)
- dry_run ok + diff ok 없으면 스키마/정책 레벨에서 거절

## 복구
- gate_status=fail → `queue.decide`에서 ZERO_STOP 수렴 + `queue.block(reason_code="GATE_FAIL")`
