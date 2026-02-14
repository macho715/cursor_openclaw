---
name: gate-runner
description: G1~G6 게이트 실행(소유=Cursor) 및 evidence 수집. gate/G1/G6/evidence 키워드면 사용.
---

# gate-runner

## Role
Stage 5 SSOT의 Gate Pipeline(G1~G6)을 실행하고 증거(evidence)를 남긴다.

## Safety
- EXEC는 needsApproval=true
- Cursor only(OpenClaw 금지)
- Gate fail 시 AUTO_MERGE 금지(DecisionRouter로 전달)

## Steps
1) EXEC 승인 확보
2) SSOT에 정의된 G1~G6를 순서대로 실행
3) 각 gate별 PASS/FAIL/SKIP 및 evidence_paths 기록
4) all_pass 산출 후 JSON 반환

## Outputs
- gate-runner branch
