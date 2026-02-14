# TRACE_EVALS_PLAN — Success/Deny/Fail, Latency, Drift Watch

## 1) 측정 지표(최소)
- success_rate = OK / total
- deny_rate = DENY / total
- fail_rate = (FAIL + ZERO_STOP) / total
- gate_fail_top = 가장 많이 실패한 gate_id Top N
- latency_ms(단계별): stop-check, queue-scan, diff-risk-scan, gate-runner 등
- drift_watch:
  - 정책/규정/SSOT 변경 감지(AGENTS.md, allowlist, audit schema 변경 시)

## 2) 감사로그(append-only) 요구 필드(최소)
- timestamp, event_id, prev_event_id
- actor(OpenClaw/Cursor/Human)
- skill, status, decision
- task_id, from_state, to_state
- tool_class, needsApproval, approval_state
- artifacts(paths)
- findings(severity/code)

## 3) Evals 샘플(권장)
- 정상 10건: inbox→done까지
- 실패 10건: gate fail, lock conflict, intake fail
- 거절 10건: approval missing, external denied
- 목표(권장):
  - Gate evidence 누락 0건
  - Denied 재시도 0건
  - AUTO_MERGE 후 롤백 0건
