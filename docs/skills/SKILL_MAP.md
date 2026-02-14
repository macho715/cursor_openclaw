# SKILL_MAP — PROJECT_BATON_v1 (Folder Queue / Option A)

## 목적
Stage 5(Agents)에서 고정된 "Folder Queue 기반 안전 자동개발 오케스트레이션"을 Stage 6에서 재사용 가능한 Skill 모듈로 분해한다.
- OpenClaw = diff/patch **제안만**
- Cursor = APPLY/TEST/COMMIT/PR/MERGE **소유**
- 안전흐름: DRY_RUN → Diff → Gate → Decision(AUTO_MERGE/PR_ONLY/ZERO_STOP) → APPLY

## Folder Queue SSOT(고정)
.autodev_queue/
- inbox/ claimed/ work/ pr/ done/ blocked/ audit/

## 호출 시퀀스(Entry → S1..S7)
Entry
  0) stop-check (G0)
     - STOP 감지 시: decision=ZERO_STOP, state=blocked 수렴
     - 이후 incident-brief + audit-append로 기록

  1) queue-scan (S1)
     - inbox/claimed/work/pr/done/blocked 카운트 + 후보 task 목록 생성

  2) claim-lock (Claim)
     - 선택 task를 claimed로 이동/락 생성
     - LOCK_CONFLICT면 incident-brief + audit-append 후 종료(재시도 금지)

  3) intake-validate (S2)
     - 필수 파일/스키마/Protected Zone/Allowlist 위반 검사
     - FAIL이면 decision=ZERO_STOP 또는 PR_ONLY(SSOT 규칙)로 수렴

  4) patch-draft-request (S3)
     - OpenClaw에 draft patch + rationale 생성 요청
     - 산출물은 work/<TASK_ID>/ 하위 "제안 아티팩트"로만 저장

  5) diff-risk-scan (S4)
     - diff lines/deletes/lockfile/protected/external-io 스캔 → risk_level 산출
     - HIGH/CRITICAL이면 decision-router에서 PR_ONLY 또는 ZERO_STOP로 제한

  6) gate-runner (G1~G6)
     - 실행/테스트/게이트는 Cursor만 수행, evidence를 지정 경로에 기록

  7) decision-router (Decision)
     - SSOT Decision Rules에 따라 AUTO_MERGE / PR_ONLY / ZERO_STOP 결정

  8) pr-merge-orchestrator (PR/Merge)
     - PR 생성/체크/merge 조건 가시화(실행은 Cursor)
     - AUTO_MERGE는 "조건 충족 시만" 수행 가능

  9) audit-append (항상)
     - 각 단계 결과를 append-only로 기록(이벤트 체인 유지)

S7(사고 수렴)
  - incident-brief: 원인/영향/복구(R1~R8 참조)/알림 템플릿 작성 → blocked 수렴
