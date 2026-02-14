---
id: skill.queue.init
name: queue.init
stage: 6.00
type: skill_spec
description: "task 초기 점검(선행조건/STOP/LOCK_CONFLICT/INPUT_MISSING 신호화) + 다음 액션 제안"
model: inherit
readonly: true
needs_approval: false
approval_owner: null
timeout_sec: 0
retry_max: 0
schemas:
  input:  docs/skills/schemas/skill.queue.init.input.schema.json
  output: docs/skills/schemas/skill.queue.init.output.schema.json
deny_conditions:
  - "없음(단, STOP/LOCK/INPUT_MISSING은 signals로 반환 → orchestrator가 block 수렴)"
audit:
  event_name: "queue.init"
  event_schema: "docs/skills/schemas/audit.event.schema.json"
artifacts_out: []
---

# skill.queue.init(task_id)

## 목적
- `.autodev_queue/<TASK_ID>/` 기준으로 진행 가능 여부 신호(OK/STOP/LOCK_CONFLICT/INPUT_MISSING)를 만든다.
- 실행 자체가 아니라 오케스트레이션용 판단 데이터를 만든다(코드 실행 없음).

## 입력
- 스키마: `docs/skills/schemas/skill.queue.init.input.schema.json`

## 출력
- 스키마: `docs/skills/schemas/skill.queue.init.output.schema.json`
- signals: OK, STOP_DETECTED, LOCK_CONFLICT, INPUT_MISSING

## 복구
- signals에 STOP/LOCK/INPUT_MISSING 포함 시 즉시 `skill.queue.block`로 수렴

## 예시 Input
```json
{ "task_id": "T-0001", "actor": "Agent" }
```
