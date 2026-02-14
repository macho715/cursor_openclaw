
# AUDIT_LOG_SCHEMA.md (SSOT)

기록 단위:
- timestamp, actor(Cursor/OpenClaw/Operator), task_id
- from_state, to_state
- decision, gate_summary, evidence_refs
- sensitive_access=false

저장 위치:
- `.autodev_queue/audit/<YYYY-MM-DD>/` (작업별 + 전역)

포맷:
- NDJSON(한 줄 = 한 이벤트) 권장
