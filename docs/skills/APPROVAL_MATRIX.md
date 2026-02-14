# APPROVAL_MATRIX — Skills × Tool Classes (Default: needsApproval=true)

## 역할 경계(불변)
- OpenClaw: diff/patch "제안만" (EXEC/PR/MERGE/External IO 금지)
- Cursor: APPLY/TEST/COMMIT/PR/MERGE 소유

| Tool Class | OpenClaw | Cursor | 기본 승인 | 비고 |
|---|---:|---:|---|---|
| READ | 허용 | 허용 | 필요 | Allowlist/Protected 검사 필수 |
| WRITE | 제한 허용 | 허용 | 필요 | OpenClaw는 work/<TASK_ID> "제안 아티팩트"만 |
| MOVE | 금지(원칙) | 허용 | 필요 | 상태 전이는 Cursor만 권장 |
| EXEC | 금지 | 허용 | 필요 | Gate/Tests |
| PR | 금지 | 허용 | 필요 | PR 생성 |
| MERGE | 금지 | 허용 | 필요 | AUTO_MERGE도 조건 충족 시만 |
| EXTERNAL | 금지 | 금지(기본) | N/A | 기본 차단(SSOT 예외만) |
| COSTLY | 제한 | 제한 | 필요 | 범위/시간 상한 명시 |

## Denied 재시도 금지(불변)
- approval state=DENIED 인 경우 동일 입력으로 재시도하지 않는다.
