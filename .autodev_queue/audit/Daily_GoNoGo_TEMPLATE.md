# Daily Go/No-Go — YYYY-MM-DD

## A) Executive
- **판정:** (Go / No-Go / PR_ONLY)
- **검증 일시:** YYYY-MM-DD HH:mm

## B) Preflight (5분)
| 항목 | 결과 | 비고 |
|------|------|------|
| B1) 18789 Port | | TcpTestSucceeded |
| B1) 11434 Port | | TcpTestSucceeded |
| B1) /v1/models 응답(data[] ≥ 1) | | OpenAI 호환 표준은 `data` |
| B2) Docker sandbox | | |
| B3) Cursor→Gateway E2E | | |

**Runbook B1 예시**
- Test-NetConnection 127.0.0.1 -Port 18789
- Test-NetConnection 127.0.0.1 -Port 11434
- `try { $r = (curl.exe -sS http://127.0.0.1:11434/v1/models | ConvertFrom-Json); if((($r.data -and $r.data.Count -ge 1) -or ($r.models -and $r.models.Count -ge 1))){"PASS"}else{"FAIL"} } catch { "FAIL" }`

## C) Queue Health
| 항목 | 결과 | 값 |
|------|------|-----|
| STOP 존재 | | |
| inbox | | |
| claimed | | |
| work | | |
| pr | | |
| done | | |
| blocked | | |
| claimed stale | | |

## D) Merge Gate
| 항목 | 결과 | 값 |
|------|------|-----|
| D1) Lines (add+del) ≤300 | | |
| D1) Binary 0 | | |
| D2) File delete 0 | | |
| D2) dep/lock 0 | | |
| D2) Allowlist OK | | |

## E) Security
| 항목 | 결과 |
|------|------|
| Token/key leak | |
| External transfer sign | |

## F) No-Go 즉시 조치
- STOP 존재 시: `New-Item .autodev_queue\STOP`
- Token leak 의심: 회전 + STOP
- Allowlist breach / dep·lockfile / 삭제·바이너리: PR_ONLY
