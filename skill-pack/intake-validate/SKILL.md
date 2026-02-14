---
name: intake-validate
description: 필수 파일/스키마/Allowlist/Protected Zone 사전 검증. validate/allowlist/protected zone 키워드면 사용.
---

# intake-validate

## Role
작업 착수 전 "불변 규칙" 위반을 조기 차단한다.

## Steps
1) READ 승인 확보
2) 필수 파일 존재/포맷 확인(SSOT 목록 기준)
3) Allowlist/Protected Zone 위반 검사(SSOT 기준)
4) FAIL이면 blocked_reason_codes를 채우고 decision-router로 넘김(또는 ZERO_STOP)

## Outputs
- intake-validate branch
