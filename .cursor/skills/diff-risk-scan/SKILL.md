---
name: diff-risk-scan
description: diff 요약 + delete/lockfile/protected/external 스캔으로 risk_level 산출. diff/risk/delete/lockfile 키워드면 사용.
---

# diff-risk-scan

## Role
Draft patch/diff를 요약하고 정책 위반 신호를 탐지해 위험도를 산출한다.

## Steps
1) READ 승인 확보(대상: draft.patch, diff)
2) 파일 변경 수/삽입/삭제 집계
3) 정책 플래그 탐지:
   - delete_detected / lockfile_touched / protected_zone_touched / allowlist_violation / external_io_attempt
4) risk_level 결정(보수적으로):
   - delete_detected 또는 allowlist_violation 또는 external_io_attempt → CRITICAL
   - protected_zone_touched 또는 lockfile_touched → HIGH
   - 그 외 → LOW/MEDIUM(SSOT 규칙 우선)

## Outputs
- diff-risk-scan branch
