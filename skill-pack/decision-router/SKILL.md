---
name: decision-router
description: Gate/Risk/STOP 결과로 AUTO_MERGE/PR_ONLY/ZERO_STOP 결정. decision/AUTO_MERGE/PR_ONLY/ZERO_STOP 키워드면 사용.
---

# decision-router

## Role
SSOT Decision Rules를 적용해 다음 행동을 결정한다.

## 최소 결정 규칙(보수적)
- STOP 감지 → ZERO_STOP
- allowlist 위반 / delete / external 시도 → ZERO_STOP
- gate fail 또는 risk HIGH/CRITICAL → PR_ONLY (또는 SSOT가 ZERO_STOP이면 그에 따름)
- 그 외 → AUTO_MERGE 후보(단, pr-merge-orchestrator에서 조건 재확인)

## Outputs
- decision-router branch
