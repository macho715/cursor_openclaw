
# APPROVAL_MATRIX.md (SSOT)

| Decision | 조건(필수) | 결과 |
|---|---|---|
| AUTO_MERGE | G0~G6 PASS + risk=LOW + 승인 완료 | Merge 가능 |
| PR_ONLY | soft fail(라인 초과/lockfile/테스트 일부 실패 등) | PR만 생성, Merge는 사람 |
| ZERO_STOP | STOP/allowlist 위반/삭제/외부전송 시도/risk=HIGH+핵심 FAIL | 즉시 중단 + blocked 격리 |

## Gate 요약
- G0 STOP
- G1 Allowlist
- G2 Max Lines(add+del ≤ 300.00)
- G3 No Delete(0.00)
- G4 No Lockfile/Deps(0.00)
- G5 Commands PASS
- G6 DRY_RUN↔APPLY 일치
