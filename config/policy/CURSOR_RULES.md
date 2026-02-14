
# CURSOR_RULES.md (SSOT)

## 0) 역할/권한 (고정)
- **Cursor = Control-Plane**: APPLY / TEST / COMMIT / PR / MERGE 소유
- **OpenClaw = Worker**: diff/patch **제안만** (적용/커밋/머지 권한 없음)

## 1) Folder Queue 상태머신(고정)
`.autodev_queue/`
- inbox/ → claimed/ → work/ → pr/ → done/
- 예외: blocked/
- STOP 존재 시: 즉시 blocked/ 격리

## 2) 안전 흐름(고정)
DRY_RUN → Diff → Gate → Decision(AUTO_MERGE/PR_ONLY/ZERO_STOP) → APPLY

## 3) STOP(킬스위치)
- 조건: `.autodev_queue/STOP` 존재
- 행동: 모든 실행 CTA 비활성 + S7 Incident로 단일 수렴 + blocked 격리

## 4) WebChat/외부전송
- 우회 경로로 간주: 기본 비활성/읽기전용
- 허용: 운영자 알림용 텍스트(마스킹)

## 5) 감사로그(append-only)
- 모든 상태 전이 기록, 수정/삭제 금지
- 상세 스키마: `AUDIT_LOG_SCHEMA.md`
