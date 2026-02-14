---
name: claim-lock
description: inbox→claimed Claim/Lock 수행 및 LOCK_CONFLICT 처리. claim/lock/conflict 키워드면 사용.
---

# claim-lock

## Role
작업을 단일 소유로 만들기 위해 Claim + Lock을 수행한다.

## Safety
- MOVE/WRITE는 needsApproval=true
- LOCK_CONFLICT 발생 시 재시도 금지(incident로 수렴)

## Steps
1) STOP 재확인(stop-check) 결과가 OK인지 확인
2) 대상 task_id를 inbox에서 claimed로 이동(SSOT 상태 전이 준수)
3) lock 파일 생성(SSOT 경로/포맷 준수)
4) 충돌이면 result=LOCK_CONFLICT로 반환 후 incident-brief로 넘김

## Outputs
- claim-lock branch
