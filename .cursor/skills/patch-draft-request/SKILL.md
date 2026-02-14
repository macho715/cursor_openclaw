---
name: patch-draft-request
description: OpenClaw에 draft patch(제안) 생성 요청/수신. draft patch/OpenClaw/proposal 키워드면 사용.
---

# patch-draft-request

## Role
OpenClaw로부터 "제안(diff/patch)"만 생성·수신한다. 적용/커밋/머지는 절대 수행하지 않는다.

## Safety
- OpenClaw: EXEC/PR/MERGE/External 금지
- WRITE는 work/<TASK_ID> 하위 "제안 아티팩트"만 허용

## Steps
1) task_id 확인(상태: claimed 또는 work)
2) OpenClaw에 생성 요청(요청 텍스트에는 PII/토큰/키 금지)
3) 산출물 저장 경로 지정:
   - .autodev_queue/work/<TASK_ID>/draft.patch
   - .autodev_queue/work/<TASK_ID>/rationale.md

## Outputs
- patch-draft-request branch
