---
id: skill.queue.claim
name: queue.claim
stage: 6.00
type: skill_spec
description: "task claim(락) 전환 제안(실제 적용은 Control-plane에서)"
model: inherit
readonly: true

needs_approval: false
approval_owner: null
timeout_sec: 0
retry_max: 0

schemas:
  input:  docs/skills/schemas/skill.queue.claim.input.schema.json
  output: docs/skills/schemas/skill.queue.claim.output.schema.json

deny_conditions:
  - "STOP_DETECTED"
  - "LOCK_CONFLICT"
  - "INPUT_MISSING"
  - "init 신호가 OK가 아님"

audit:
  event_name: "queue.claim"
  event_schema: "docs/skills/schemas/audit.event.schema.json"

artifacts_out: []
---

# skill.queue.claim(task_id)

## 목적
- 작업을 claimed 상태로 전환하기 위한 **명령/요청**을 만든다.
- Stage6에서는 "실행"이 아니라 **제안/요청 패킷**을 산출한다.

## 입력/출력
- input schema: `docs/skills/schemas/skill.queue.claim.input.schema.json`
- output schema: `docs/skills/schemas/skill.queue.claim.output.schema.json`

## Deny (Hard)
- STOP_DETECTED, LOCK_CONFLICT, INPUT_MISSING
- init 결과가 OK가 아닌 경우(오케스트레이터가 deny_reason 부여)

## 복구
- LOCK_CONFLICT → `queue.block(reason_code="LOCK_CONFLICT")` 권고
- STOP → `queue.block(reason_code="STOP_DETECTED")` 권고
- INPUT_MISSING → `queue.block(reason_code="INPUT_MISSING")` 권고

## 감사로그
- event_name: `queue.claim`

## 예시

### Input
```json
{ "task_id": "T-0001", "actor": "Agent" }
```

### Output (ok)
```json
{
  "task_id": "T-0001",
  "status": "ok",
  "expected_state": "claimed",
  "audit_event": {
    "event_name": "queue.claim",
    "task_id": "T-0001",
    "actor": "Agent",
    "phase": "PROPOSE",
    "severity": "INFO",
    "ts": "2026-02-14T00:00:10Z"
  }
}
```
