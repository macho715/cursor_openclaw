---
name: stop-check
description: STOP(킬스위치) 감지 후 즉시 ZERO_STOP 수렴. STOP/kill switch/blocked/중단 키워드가 나오면 사용.
---

# stop-check

## Role
STOP(킬스위치) 신호를 최우선으로 탐지하고, 발견 시 즉시 ZERO_STOP으로 수렴한다.

## In-Scope
- `.autodev_queue/**` 및 SSOT가 지정한 STOP sentinel 검사
- STOP 발견 시 blocked 격리(계획만) + incident/audit 트리거

## Out-of-Scope
- 임의의 경로에서 STOP 의미 추정(SSOT 외)
- External IO/업로드/알림 전송

## Inputs
- queue_root: `.autodev_queue`
- (선택) task_id

## Steps
1) needsApproval=true로 READ 범위 승인 확보
2) SSOT 지정 STOP sentinel을 검사(없으면 `.autodev_queue/STOP`만 기본 검사)
3) STOP 발견 시:
   - status=ZERO_STOP, decision=ZERO_STOP
   - 다음 단계: `incident-brief`, `audit-append`, state=blocked 수렴

## Outputs
- JSON 1개(스키마): `docs/skills/schemas/skill_outputs.schema.json`의 stop-check branch

## Safety
- Read도 승인 필요
- STOP 발견 시 다른 작업 금지(즉시 종료)
