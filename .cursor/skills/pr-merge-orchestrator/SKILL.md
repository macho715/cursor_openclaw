---
name: pr-merge-orchestrator
description: PR 생성/체크/merge 조건을 계획으로 정리(실행은 Cursor). PR/merge/AUTO_MERGE/PR_ONLY 키워드면 사용.
---

# pr-merge-orchestrator

## Role
결정(AUTO_MERGE/PR_ONLY)에 따라 "다음 실행 단계(계획)"를 산출한다.
- 실제 PR 생성/merge는 Cursor 소유 + 승인 필요

## Steps
- mode=PR_ONLY:
  1) PR 생성
  2) checks 통과 확인
  3) 리뷰/승인 후 merge 가능
- mode=AUTO_MERGE:
  1) 마지막 위험 재확인(삭제/Protected/External/lockfile 금지)
  2) Gate all PASS
  3) 조건 충족 시만 merge 가능

## Outputs
- pr-merge-orchestrator branch
