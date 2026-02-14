---
id: skill.queue.diff
name: queue.diff
stage: 6.00
type: skill_spec
description: "Diff 생성 요청(승인 필요, dry_run 선행 필수)"
model: inherit
readonly: true

needs_approval: true
approval_owner: "Cursor"
timeout_sec: 60
retry_max: 1

schemas:
  input:  docs/skills/schemas/skill.queue.diff.input.schema.json
  output: docs/skills/schemas/skill.queue.diff.output.schema.json

preconditions:
  - "run_approved.json 존재"
  - "dry_run.status == ok"
deny_conditions:
  - "run_approved.json 부재"
  - "dry_run 산출물 누락"
  - "STOP_DETECTED"
  - "LOCK_CONFLICT"
  - "INPUT_MISSING"

audit:
  event_name: "queue.diff"
  event_schema: "docs/skills/schemas/audit.event.schema.json"

artifacts_out:
  - "artifacts/<TASK_ID>/diff.json"
---

# skill.queue.diff(task_id)

## 목적
- DRY_RUN 결과 이후 diff를 생성하고 evidence(`diff.json`)를 남긴다.

## 승인(필수)
- `.autodev_queue/<TASK_ID>/approval/run_approved.json`

## 선행조건(Hard)
- dry_run.status == ok
- dry_run artifact path 제공

## 입력/출력
- input: `docs/skills/schemas/skill.queue.diff.input.schema.json`
- output: `docs/skills/schemas/skill.queue.diff.output.schema.json`

## 실패/재시도
- 최대 1.00회(Transient error만)

## 복구
- denied → `queue.block(reason_code="RUN_APPROVAL_DENIED")`
- fail(재시도 후) → `queue.block(reason_code="EXEC_FAIL")`

## 예시

### Input
```json
{
  "task_id": "T-0001",
  "actor": "Cursor",
  "run_approval_path": ".autodev_queue/T-0001/approval/run_approved.json",
  "dry_run_artifact_path": "artifacts/T-0001/dry_run.json"
}
```

### Output (ok)
```json
{
  "task_id": "T-0001",
  "status": "ok",
  "artifact_path": "artifacts/T-0001/diff.json",
  "audit_event": {
    "event_name": "queue.diff",
    "task_id": "T-0001",
    "actor": "Cursor",
    "phase": "RUN",
    "severity": "INFO",
    "ts": "2026-02-14T00:02:00Z",
    "artifact_paths": ["artifacts/T-0001/diff.json"]
  }
}
```
