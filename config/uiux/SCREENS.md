
# SCREENS.md
(화면 7개 고정: S1~S7)

## 공통 UI 규칙(고정)
- 상단 Global Bar: Queue 상태 + STOP 배지 + 현재 Task + 승인 상태(Approved/Not Approved)
- 좌측: Queue 탭(inbox/claimed/work/pr/done/blocked)
- 우측 하단: AuditDrawer(읽기전용)
- 위험요소(Protected/External IO/Allowlist 위반)는 항상 “시각+텍스트” 동시 표기

---

## S1. Queue Monitor
목적: 큐 요약 + 작업 선택/Claim + STOP 감지
표시:
- 폴더별 카운트, 최근 변경 시각, stuck(장기 work) 경고
- STOP 감지 시: StopBanner + 모든 CTA 비활성
액션:
- View Task, Claim Task(락), Open Incident

상태:
- Empty(inbox=0), Lock Conflict, STOP, Loading/Error

---

## S2. Task Detail
목적: 인테이크 파일(task/acceptance/risk/allowlist/commands) 검증
표시:
- task.md(요약/전체), acceptance.md 체크리스트, risk.json 요약 뱃지
- allowlist.txt(허용 경로), commands.md(lint/test/build)
- “필수 입력 누락” 경고 + 자동 blocked 유도
액션:
- Edit(문서 편집은 별도 권한; 기본은 ‘수정 제안’ 형태)
- Open Plan

상태:
- INPUT_MISSING, INVALID_RISK, DENY_BY_PROTECTED

---

## S3. Plan
목적: 변경 범위/테스트/롤백/리스크를 “사람이 읽고 승인 가능한” 1장으로 고정
구성:
- Scope: 변경 파일/경로(allowlist 내)
- Test Strategy: lint/test/build + 선택(E2E/a11y)
- Rollback: revert 전략(커밋/PR 단위)
- Risk: LOW/MED/HIGH + 왜 그렇게 분류했는지
액션:
- Request Patch Draft(OpenClaw)
- Abort/Back

상태:
- Awaiting Draft, STOP, Missing Commands

---

## S4. Patch Diff (OpenClaw 제안 전용)
목적: diff 리뷰 + 위험 스캔 결과 확인(읽기전용)
표시(상단 요약):
- Files changed N, Lines(add+del) N, Deletes N, Lockfile changes N
- Allowlist hit-rate, Protected Zone hit 여부
중앙:
- DiffViewer(파일별)
하단:
- “Run Gates” (Cursor 전용), “Request Redraft”

상태:
- DIFF_PARSE_FAIL, POLICY_VIOLATION_HARD/SOFT

---

## S5. Gate Results
목적: Gate PASS/FAIL을 표 + Evidence로 고정
표(필수):
- G0 STOP
- G1 Allowlist
- G2 Max Lines(≤300.00)
- G3 No Delete
- G4 No Lockfile/Deps
- G5 Commands PASS
- G6 DRY_RUN↔APPLY 일치
Evidence:
- 로그 링크/해시(텍스트), 실행 시각, 실행자(Cursor)

액션:
- Decide(AUTO_MERGE / PR_ONLY / ZERO_STOP)
- Re-run failed gates only

---

## S6. PR & Merge
목적: PR 생성/상태체크/Auto-merge 조건 가시화
표시:
- PR 상태(Open/Checks Running/Checks Failed/Mergeable)
- Auto-merge “가능/불가” 사유(조건 리스트)
액션:
- Create PR
- Merge (AUTO_MERGE 조건 충족 + 승인 완료 시만)
- Move to blocked (수동介入)

---

## S7. Incident
목적: ZERO_STOP/STOP/보안 위반/게이트 하드 실패의 단일 진입점
표시:
- Incident 요약(원인, 영향 범위, 마지막 정상 시점)
- Fail-safe 로그(append-only)
- 복구 체크리스트(재시도/롤백/알림)
액션:
- Retry(허용 시)
- Rollback
- Notify Operator(알림 텍스트만)
- Close Incident(운영자 확인 필요)
