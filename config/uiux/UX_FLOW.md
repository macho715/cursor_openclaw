
# UX_FLOW.md

## 0) 원칙(고정)

OpenClaw: diff/patch “제안만” (코드 적용/커밋/머지 권한 없음)

Cursor: APPLY/TEST/COMMIT/PR/MERGE “소유”

안전 흐름: DRY_RUN → Diff → Gate → Decision(AUTO_MERGE/PR_ONLY/ZERO_STOP) → APPLY

WebChat/외부전송: 우회 경로로 간주, 기본 비활성/읽기전용

STOP(킬스위치): 존재 시 즉시 중단 + 모든 작업 blocked로 격리

감사로그: append-only, 모든 상태 전이 기록

## 1) Folder Queue SSOT(고정)
.autodev_queue/
inbox/        # 신규 작업(폴더 단위)
claimed/      # 락(Claim)된 작업
work/         # 패치 초안 생성/검증 진행
pr/           # PR 생성 후 상태 추적
done/         # merge + post-check 완료
blocked/      # STOP / ZERO_STOP / 수동介入 필요
audit/        # append-only 감사로그(작업별 + 전역)
STOP/         # (폴더 또는 파일) 존재 시 전면 중단

## 2) Task Folder Contract(인테이크 최소 구성)

inbox/<TASK_ID>/
  task.md
  acceptance.md
  risk.json
  allowlist.txt
  commands.md
  notes.md (선택)

## 3) 메인 플로우(정상 경로)
Entry → S1 → Claim → S2 → S3 → Draft(OpenClaw) → S4 → S5 → Decision → S6 → done/blocked

## 4) STOP(킬스위치) 플로우(강제)
조건: .autodev_queue/STOP 존재
- 모든 CTA 비활성
- 진행 중 작업 blocked 격리
- S7에서만 복구 제공

## 5) Gate Pipeline(필수)
G0 STOP / G1 Allowlist / G2 Max Lines / G3 No Delete / G4 No Lockfile/Deps / G5 Commands PASS / G6 DRY_RUN↔APPLY

## 6) Decision Rules(고정)
AUTO_MERGE / PR_ONLY / ZERO_STOP

## 7) Recovery Paths(최소)
R1~R8 (LOCK_CONFLICT, INPUT_MISSING, PATCH_INVALID, GATE_FAIL_SOFT/HARD, PARTIAL_FAIL, STOP_TRIGGERED_MIDWAY, INCIDENT_CLOSE)

## 8) 감사로그(append-only) 계약
(timestamp, actor, task_id, from_state, to_state, decision, gate_summary, evidence_refs, sensitive_access=false)
