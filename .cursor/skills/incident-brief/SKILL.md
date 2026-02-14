---
name: incident-brief
description: S7 수렴 사고 리포트(원인/영향/복구 R1~R8 참조/알림 템플릿). incident/S7/recovery 키워드면 사용.
---

# incident-brief

## Role
ZERO_STOP/FAIL/DENY 상황을 "사고 텍스트"로 구조화하고 blocked로 수렴한다.

## Steps
1) WRITE 승인 확보
2) incident_id 생성(세션 내 유니크)
3) headline/impact/actions/recovery_refs(R#) 작성
4) notify_template 포함(외부 전송은 금지, 텍스트만)

## Outputs
- incident-brief branch
