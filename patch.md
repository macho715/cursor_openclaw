diff --git a/.cursor/commands/setup-init.md b/.cursor/commands/setup-init.md
new file mode 100644
index 0000000..9b7b3fd
--- /dev/null
+++ b/.cursor/commands/setup-init.md
@@ -0,0 +1,189 @@
+# /setup:init
+SSOT 로드 + 큐 템플릿 DRY_RUN/적용 가이드
+
+Status: active  
+Timezone: Asia/Dubai  
+Scope: 문서/설정 텍스트만(구현/실행/배포 금지)  
+
+---
+
+## 0) 목적
+
+- Stage 3(Cursor Project Setting)에서 **SSOT/Queue/정책 문서**가 준비되었는지 확인한다.
+- 미비 시 **patch-only(유니파이드 diff)** 로 “생성/보완안”만 제안한다(자동 적용 금지).
+- STOP(킬스위치)와 allowlist/민감정보 규칙을 선행 점검한다.
+
+참조(정책 SSOT):
+- `docs/policy/CURSOR_RULES.md`
+- `docs/policy/TOOL_POLICY.md`
+- `docs/policy/APPROVAL_MATRIX.md`
+- `docs/policy/AUDIT_LOG_SCHEMA.md`
+- `.cursor/rules/AUTODEV_POLICY.md`
+
+---
+
+## 1) INPUT REQUIRED (없으면 UNKNOWN 유지)
+
+| Item | Value |
+|---|---|
+| 기본 브랜치명(main/master 등) | UNKNOWN |
+| Required status checks 목록 | UNKNOWN |
+| allowlist_write 경로 | UNKNOWN |
+
+---
+
+## 2) 선행 조건(Preconditions)
+
+| Check | PASS 조건 | FAIL 시 |
+|---|---|---|
+| STOP 존재 여부 | `.autodev_queue/STOP` 미존재 | 즉시 `ZERO_STOP` + `blocked/` 격리 |
+| 민감정보 | 토큰/키/내부 URL/실경로 원문 0.00 | 즉시 `ZERO_STOP` |
+| 스코프 | 정책/커맨드 문서 범위만 | 범위 이탈 시 `PR_ONLY` 또는 `ZERO_STOP` |
+
+---
+
+## 3) DRY_RUN 절차(점검만)
+
+1. **SSOT 로드**
+   - `MANIFEST.json`의 `stage_current/stage_next` 확인
+   - `BATON_CURRENT.md` 확인
+2. **Folder Queue 존재 점검**
+   - `.autodev_queue/` 및 하위 상태 폴더 존재 여부만 점검:
+     - `inbox/ claimed/ work/ pr/ done/ blocked/ audit/`
+   - 비어있는 폴더는 Git 추적이 어려우므로(빈 디렉토리) 필요 시 `.gitkeep`로만 제안한다.
+3. **Daily Go/No-Go 템플릿 점검**
+   - `.autodev_queue/audit/Daily_GoNoGo_TEMPLATE.md` 존재 여부 확인
+4. **정책 문서 존재 점검**
+   - `docs/policy/*.md` 4종 + `.cursor/rules/AUTODEV_POLICY.md`
+5. **결과 기록(텍스트-only)**
+   - 결과는 “보고서”로만 남긴다(자동 수정 금지):
+     - 권장: `.autodev_queue/audit/setup_init_report_YYYY-MM-DD.md`
+
+---
+
+## 4) APPLY_REQUEST 절차(패치 제안만)
+
+DRY_RUN 결과 미비가 있으면 아래만 수행한다:
+
+- **patch-only** 로 “생성/보완 diff”를 제안한다.
+- 실제 `apply/test/commit/merge`는 Cursor(Control-Plane)에서 **별도 승인 후** 수행한다.
+
+생성 대상(예시):
+- `.autodev_queue/audit/Daily_GoNoGo_TEMPLATE.md` (없을 때만)
+- `.autodev_queue/**/.gitkeep` (폴더 구조 고정이 필요할 때만)
+- `.cursor/commands/*.md` (커맨드 문서 보완)
+
+---
+
+## 5) 산출물(Outputs)
+
+| Output | Path | Notes |
+|---|---|---|
+| Init Report | `.autodev_queue/audit/setup_init_report_YYYY-MM-DD.md` | 텍스트-only |
+| Audit Log(권장) | `.autodev_queue/audit/audit_log_YYYY-MM-DD.jsonl` | append-only |
+
+---
+
+## 6) 감사로그(append-only) 기록 템플릿
+
+`docs/policy/AUDIT_LOG_SCHEMA.md` 준수. 예시:
+
+```json
+{
+  "date": "2026-02-14",
+  "actor": "Cursor",
+  "queue_state_from": "inbox",
+  "queue_state_to": "inbox",
+  "decision": "PR_ONLY",
+  "gate_results": {
+    "G0_STOP": "PASS",
+    "G4_ALLOWLIST": "UNKNOWN",
+    "G5_SECRETS": "PASS",
+    "REMOTE_GATE": "UNKNOWN"
+  },
+  "evidence_refs": ["POLICY_SSOT_PRESENT", "QUEUE_STRUCTURE_CHECKED"],
+  "masked_notes": "base_branch=UNKNOWN; required_checks=UNKNOWN; allowlist_write=UNKNOWN"
+}
+```
+
+---
+
+## 7) 실패/중단 기준(ZERO_STOP)
+
+| Trigger | Reason | Action |
+|---|---|---|
+| STOP 존재 | 킬스위치 우선 | 즉시 중단 + `blocked/` 격리 + 감사로그 |
+| 민감정보 원문 감지 | NDA/보안 위반 | 즉시 중단 + `<MASKED>` 처리 + 감사로그 |
+| allowlist 위반 | 스코프 오염 | 즉시 중단 + PR_ONLY 금지(사안 따라) |
+
diff --git a/.cursor/commands/queue-claim.md b/.cursor/commands/queue-claim.md
new file mode 100644
index 0000000..8a2a5c4
--- /dev/null
+++ b/.cursor/commands/queue-claim.md
@@ -0,0 +1,215 @@
+# /queue:claim
+inbox→claimed (락/충돌/STOP 체크)
+
+Status: active  
+Timezone: Asia/Dubai  
+Scope: 문서/설정 텍스트만(구현/실행/배포 금지)  
+
+---
+
+## 0) 목적
+
+- `.autodev_queue/inbox/<JOB_ID>/` 작업을 **단일 작업자(Cursor)** 가 안전하게 점유(claim)한다.
+- 충돌/중복 작업/STOP 존재 여부를 확인하고, 위반 시 즉시 `ZERO_STOP` 또는 `PR_ONLY`로 전환한다.
+
+---
+
+## 1) INPUTS
+
+| Item | Value |
+|---|---|
+| JOB_ID | `<JOB_ID>` |
+| From | `.autodev_queue/inbox/<JOB_ID>/` |
+| To | `.autodev_queue/claimed/<JOB_ID>/` |
+| Actor | `Cursor` (고정) |
+
+---
+
+## 2) 선행 조건(Preconditions)
+
+| Check | PASS 조건 | FAIL 시 |
+|---|---|---|
+| STOP | `.autodev_queue/STOP` 미존재 | `ZERO_STOP` |
+| 존재 | inbox에 `<JOB_ID>` 존재 | `PR_ONLY`(요청 재확인) |
+| 중복 claim | claimed/work/pr/done/blocked에 동일 JOB_ID 없음 | `PR_ONLY` 또는 `ZERO_STOP` |
+
+---
+
+## 3) DRY_RUN 절차(점검만)
+
+1. STOP 존재 여부 확인  
+2. `<JOB_ID>`가 inbox에 존재하는지 확인  
+3. 동일 `<JOB_ID>`가 다른 상태 폴더에 존재하는지 확인  
+4. 충돌이 없으면 “claim 가능”으로 판정하고, 아래 메타정보를 준비한다:
+   - `claim_time=YYYY-MM-DD`
+   - `actor=Cursor`
+   - `reason=작업 착수`
+
+---
+
+## 4) APPLY_REQUEST 절차(이동/락은 Cursor 소유)
+
+> Stage 3 정책 문서에서는 “절차”만 정의한다. 실제 이동/적용은 승인 후 Cursor가 수행한다.
+
+1. inbox → claimed 로 작업 폴더 이동(원자적 이동을 우선)  
+2. claimed 폴더 내부에 **락 파일** 생성(권장):
+   - `CLAIM.json` 또는 `CLAIM.md`
+3. 감사로그(append-only) 기록
+
+락 파일 예시(민감정보 금지):
+
+```json
+{
+  "job_id": "<JOB_ID>",
+  "claimed_on": "2026-02-14",
+  "actor": "Cursor",
+  "notes": "<MASKED>"
+}
+```
+
+---
+
+## 5) 충돌 처리(Conflict Handling)
+
+### 5.1 이미 claimed/work/pr에 존재
+- **중복 작업 위험**으로 `PR_ONLY` 기본값
+- 필요 시 `/incident:recover`로 전환하여 “스테일 claim(유령 락)” 여부 확인
+
+### 5.2 blocked에 존재
+- STOP 또는 ZERO_STOP 이력 가능성이 높으므로:
+  - Operator 승인 없이는 재개 금지
+  - 감사로그/evidence를 먼저 확인
+
+### 5.3 done에 존재
+- 종료된 작업이므로 재오픈 금지(새 JOB_ID로 재등록)
+
+---
+
+## 6) 산출물(Outputs)
+
+| Output | Path | Notes |
+|---|---|---|
+| 작업 폴더 위치 | `.autodev_queue/claimed/<JOB_ID>/` | 상태 전이 |
+| 락 파일 | `claimed/<JOB_ID>/CLAIM.json` | 권장 |
+| 감사로그 | `.autodev_queue/audit/audit_log_YYYY-MM-DD.jsonl` | REQUIRED |
+
+---
+
+## 7) 감사로그(append-only) 예시
+
+```json
+{
+  "date": "2026-02-14",
+  "actor": "Cursor",
+  "queue_state_from": "inbox",
+  "queue_state_to": "claimed",
+  "decision": "PR_ONLY",
+  "gate_results": {
+    "G0_STOP": "PASS",
+    "G6_APPEND_ONLY": "PASS"
+  },
+  "evidence_refs": ["QUEUE_CLAIM_ATTEMPT", "NO_CONFLICT_DETECTED"],
+  "masked_notes": "job_id=<MASKED>"
+}
+```
+
+---
+
+## 8) No-Go / ZERO_STOP 트리거
+
+| Trigger | Action |
+|---|---|
+| STOP 존재 | 즉시 `ZERO_STOP` + blocked 격리 |
+| allowlist/민감정보 위반 발견 | 즉시 `ZERO_STOP` |
+
diff --git a/.cursor/commands/queue-open-plan.md b/.cursor/commands/queue-open-plan.md
new file mode 100644
index 0000000..a4a7db0
--- /dev/null
+++ b/.cursor/commands/queue-open-plan.md
@@ -0,0 +1,230 @@
+# /queue:open-plan
+S3 Plan 1장 요약 생성(범위/테스트/롤백/리스크)
+
+Status: active  
+Timezone: Asia/Dubai  
+Scope: 문서/설정 텍스트만(구현/실행/배포 금지)  
+
+---
+
+## 0) 목적
+
+- `claimed/<JOB_ID>` 작업에 대해 **“1장짜리 계획(Plan)”** 을 고정 포맷으로 만든다.
+- Plan은 이후 OpenClaw patch 제안의 **입력(스코프/가드/테스트/롤백)** 이 된다.
+
+---
+
+## 1) INPUTS
+
+| Item | Value |
+|---|---|
+| JOB_ID | `<JOB_ID>` |
+| Queue Path | `.autodev_queue/claimed/<JOB_ID>/` |
+| allowlist_write | UNKNOWN |
+| 기본 브랜치명 | UNKNOWN |
+| Required checks | UNKNOWN |
+
+---
+
+## 2) Plan 산출 위치(권장)
+
+| File | Path | Notes |
+|---|---|---|
+| PLAN | `claimed/<JOB_ID>/PLAN.md` | 1장 요약 |
+| INTENT LOCK(권장) | `claimed/<JOB_ID>/intent_lock.yml` | “무엇을 바꾸지 않는가” |
+| EVIDENCE(권장) | `claimed/<JOB_ID>/EVIDENCE.md` | 링크 원문 금지(식별자만) |
+
+---
+
+## 3) Plan 작성 절차(DRY_RUN → 문서 작성)
+
+1. 요청(REQUEST) 확인  
+   - 작업 폴더 내 요청 텍스트가 없다면: `UNKNOWN`으로 남기고 PR_ONLY로 제한한다.
+2. 범위(Scope) 정의  
+   - 변경 대상 경로는 allowlist_write 내부로 제한(UNKNOWN이면 “정책 산출물 경로”로만 제한)
+3. 비목표(Non-goals) 명시  
+   - 대규모 리라이트 금지
+   - 실행/배포/운영 변경 금지(Stage 3)
+4. 테스트/검증 계획 정의(명령은 예시로만)
+   - 정책/문서 단계에서는 “검증 항목”만 정의
+5. 롤백/복구 정의
+   - 실패 시 `blocked/` 격리, PR_ONLY로 전환
+6. 리스크/게이트 연결
+   - G0~G6 중 어떤 게이트가 핵심인지 명시
+
+---
+
+## 4) PLAN.md 템플릿(고정)
+
+아래 포맷을 그대로 사용한다:
+
+```md
+# PLAN — <JOB_ID>
+
+## A) Scope (허용 변경)
+- allowlist_write: UNKNOWN
+- 변경 대상(예): docs/policy/**, .cursor/** (Stage 3 범위)
+
+## B) Out of Scope (금지)
+- 코드 구현/실행/배포
+- 파일 삭제(0.00)
+- dep/lockfile 변경(0.00)
+- 이진 변경(0.00)
+- 토큰/키/내부 URL/실경로 원문 노출
+
+## C) Deliverables
+- patch-only(유니파이드 diff)로 문서 생성/수정
+- 감사로그 append-only 기록
+
+## D) Validation (예시, 실행 지시 아님)
+- Gate: G0~G6 결과표 생성
+- 포맷: 요약→승인→patch-only→검증/로그
+
+## E) Rollback / Recovery
+- 실패 시: decision=ZERO_STOP, blocked 격리, audit 기록
+- 재개는 Operator 승인 필요(사유/위험/다음조치)
+
+## F) Risks / Gates Focus
+- G0 STOP: 최우선
+- G4 allowlist: UNKNOWN이면 AUTO_MERGE 금지
+- G5 secrets: 1.00건이라도 즉시 ZERO_STOP
+
+## G) Evidence Refs (원문 링크 금지)
+- REQUEST_REF: <MASKED>
+- POLICY_REF: CURSOR_RULES/TOOL_POLICY/APPROVAL_MATRIX/AUDIT_LOG_SCHEMA
+```
+
+---
+
+## 5) intent_lock.yml(권장)
+
+요지는 “바꾸지 않을 것”을 잠그는 것이다(예시):
+
+```yml
+job_id: "<JOB_ID>"
+locked:
+  - "no_code_implementation"
+  - "no_delete_files"
+  - "no_dep_lock_changes"
+  - "no_binary_changes"
+  - "no_secrets_or_internal_urls"
+unknowns:
+  - "base_branch"
+  - "required_status_checks"
+  - "allowlist_write"
+```
+
+---
+
+## 6) 산출물(Outputs)
+
+| Output | Path |
+|---|---|
+| PLAN.md | `claimed/<JOB_ID>/PLAN.md` |
+| intent_lock.yml(권장) | `claimed/<JOB_ID>/intent_lock.yml` |
+| EVIDENCE.md(권장) | `claimed/<JOB_ID>/EVIDENCE.md` |
+
diff --git a/.cursor/commands/request-patch-draft.md b/.cursor/commands/request-patch-draft.md
new file mode 100644
index 0000000..4e8bd8b
--- /dev/null
+++ b/.cursor/commands/request-patch-draft.md
@@ -0,0 +1,249 @@
+# /queue:request-patch-draft
+OpenClaw에게 patch 제안 생성 요청(제안만)
+
+Status: active  
+Timezone: Asia/Dubai  
+Scope: 문서/설정 텍스트만(구현/실행/배포 금지)  
+
+---
+
+## 0) 목적
+
+- OpenClaw(Worker)에게 **유니파이드 diff “제안”** 만 생성하도록 요청한다.
+- OpenClaw는 **apply/commit/merge 권한이 없으며**, 결과는 항상 검증(Gates) 대상이다.
+
+---
+
+## 1) 입력(Inputs)
+
+| Item | Value |
+|---|---|
+| JOB_ID | `<JOB_ID>` |
+| Plan | `claimed/<JOB_ID>/PLAN.md` |
+| 정책 SSOT | `docs/policy/*` + `.cursor/rules/AUTODEV_POLICY.md` |
+| allowlist_write | UNKNOWN |
+
+---
+
+## 2) 사전 정리(Sanitization, 필수)
+
+OpenClaw에 전달하기 전 반드시:
+
+- 토큰/키/내부 URL/실경로 원문은 모두 `<MASKED>` 처리
+- 개인 식별 정보(이메일/전화번호/주소 등) `<MASKED>`
+- Evidence는 “식별자”로만(원문 링크 금지)
+
+---
+
+## 3) 요청 메시지 템플릿(OpenClaw용)
+
+> 아래는 “복붙용 템플릿”이며, 자동 실행 지시가 아니다.
+
+```md
+ROLE
+- 너는 OpenClaw(Worker)다. diff/patch 제안만 가능하다. apply/commit/merge 금지.
+
+CONTEXT (SSOT)
+- Queue: .autodev_queue (inbox→claimed→work→pr→done/blocked)
+- Policy: docs/policy/*, .cursor/rules/AUTODEV_POLICY.md
+- Job: <JOB_ID>
+
+TASK
+- 아래 변경을 patch-only(유니파이드 diff)로만 제안하라.
+- 신규 파일 생성은 --- /dev/null 형태로 제안하라.
+
+CONSTRAINT (HARD)
+- 코드 구현/실행/배포 금지
+- 파일 삭제 0.00, dep/lockfile 변경 0.00, 이진 변경 0.00
+- allowlist_write=UNKNOWN이면: docs/policy/** 및 .cursor/** 외 변경 금지
+- 민감정보 원문(토큰/키/내부 URL/실경로) 금지: 발견 시 `<MASKED>`
+- 출력은 오직 "unified diff"만(설명 문장 금지)
+
+INPUTS
+- PLAN.md (요약):
+  <붙여넣기: claimed/<JOB_ID>/PLAN.md>
+```
+
+---
+
+## 4) 기대 출력(Outputs)
+
+OpenClaw 출력은 아래만 허용:
+- **유니파이드 diff 단독**
+- diff 외 텍스트(설명/요약/명령) 금지
+
+---
+
+## 5) 실패 처리
+
+| Case | Action |
+|---|---|
+| diff 외 문장 포함 | 결과 폐기 + 재요청(PR_ONLY) |
+| 스코프/삭제/dep/lock 위반 | 즉시 `ZERO_STOP` 후보로 표기 + `/queue:run-gates`에서 FAIL 처리 |
+| 민감정보 원문 포함 | 즉시 `ZERO_STOP` + `<MASKED>` 정리 후 재요청 |
+
diff --git a/.cursor/commands/queue-run-gates.md b/.cursor/commands/queue-run-gates.md
new file mode 100644
index 0000000..6a7b8d1
--- /dev/null
+++ b/.cursor/commands/queue-run-gates.md
@@ -0,0 +1,283 @@
+# /queue:run-gates
+G0~G6 실행 + Evidence 수집
+
+Status: active  
+Timezone: Asia/Dubai  
+Scope: 문서/설정 텍스트만(구현/실행/배포 금지)  
+
+---
+
+## 0) 목적
+
+- 생성된 diff(패치 제안)를 **정량/정성 Gate(G0~G6)** 로 평가한다.
+- 결과는 Decision(`/queue:decide`)의 입력으로 사용한다.
+
+참조(정책 SSOT):
+- `docs/policy/CURSOR_RULES.md`
+- `docs/policy/APPROVAL_MATRIX.md`
+- `docs/policy/TOOL_POLICY.md`
+- `docs/policy/AUDIT_LOG_SCHEMA.md`
+
+---
+
+## 1) 입력(Inputs)
+
+| Item | Value |
+|---|---|
+| JOB_ID | `<JOB_ID>` |
+| Patch(diff) | `<DIFF_REF>` |
+| 오늘 audit=Go | UNKNOWN |
+| allowlist_write | UNKNOWN |
+| Required status checks | UNKNOWN |
+
+---
+
+## 2) Gate 정의(G0~G6)
+
+| Gate | Name | PASS 조건(요약) | FAIL 시 |
+|---|---|---|---|
+| G0 | STOP | STOP 미존재 | ZERO_STOP |
+| G1 | Daily Go/No-Go | 오늘 audit=Go | AUTO_MERGE 금지(PR_ONLY) |
+| G2 | Patch Size | 추가+삭제 라인 ≤ 300.00 | AUTO_MERGE 금지(PR_ONLY) |
+| G3 | File Safety | 삭제 0.00, dep/lock 0.00, 이진 0.00 | PR_ONLY 또는 ZERO_STOP |
+| G4 | Path Allowlist | allowlist_write 내부만 | ZERO_STOP |
+| G5 | Secrets/NDA | 민감정보 원문 0.00 | ZERO_STOP |
+| G6 | Append-only | 감사로그 append-only 준수 | ZERO_STOP |
+
+REMOTE_GATE(별도):
+- Protected branch + Required status checks 상태는 **CONFIRMED/UNKNOWN** 분리
+- UNKNOWN이면 AUTO_MERGE에서 PASS로 간주 금지
+
+---
+
+## 3) DRY_RUN 절차(평가만)
+
+1. STOP 확인(G0)  
+2. 오늘자 Daily audit 확인(G1)  
+3. diff 메트릭 산출(G2)
+   - lines_added, lines_deleted를 2.00자리로 기록
+4. 파일 변경 타입 확인(G3)
+   - 삭제/dep/lock/이진 여부 체크
+5. 경로 allowlist 확인(G4)
+   - allowlist_write=UNKNOWN이면 “정책 산출물 경로(docs/policy/**, .cursor/**)”만 허용
+6. 민감정보 스캔(G5)
+   - 토큰/키/내부 URL/실경로 원문 감지 시 FAIL
+7. 감사로그 규칙(G6)
+   - 기존 로그 수정/삭제 시도 여부 확인(append-only 위반)
+8. REMOTE_GATE 상태 기록
+   - CONFIRMED/UNKNOWN만 기록(링크 원문 금지)
+
+---
+
+## 4) 산출물(Outputs)
+
+| Output | Path | Notes |
+|---|---|---|
+| Gate 결과표 | `work/<JOB_ID>/GATES.md` | 표 형태 권장 |
+| Gate 결과 JSON | `work/<JOB_ID>/gate_results.json` | 권장 |
+| Evidence | `work/<JOB_ID>/EVIDENCE.md` | 식별자만 |
+| 감사로그 | `.autodev_queue/audit/audit_log_YYYY-MM-DD.jsonl` | append-only |
+
+---
+
+## 5) GATES.md 포맷(권장)
+
+```md
+# GATES — <JOB_ID>
+
+| Gate | Result | Metric/Note |
+|---|---|---|
+| G0_STOP | PASS/FAIL | stop_present=false |
+| G1_DAILY_AUDIT | PASS/FAIL/UNKNOWN | daily=Go? |
+| G2_PATCH_SIZE | PASS/FAIL | added=0.00, deleted=0.00 |
+| G3_FILE_SAFETY | PASS/FAIL | del=0.00, dep_lock=0.00, bin=0.00 |
+| G4_ALLOWLIST | PASS/FAIL/UNKNOWN | allowlist_write=UNKNOWN |
+| G5_SECRETS | PASS/FAIL | secrets=0.00 |
+| G6_APPEND_ONLY | PASS/FAIL | ok |
+| REMOTE_GATE | PASS/FAIL/UNKNOWN | protected=UNKNOWN, checks=UNKNOWN |
+```
+
+---
+
+## 6) Evidence 수집 규칙
+
+- 원문 링크/내부 URL은 기록 금지
+- Evidence는 “키/식별자”로만 기록:
+  - `GH_PROTECTED_BRANCH_DOC`
+  - `OLLAMA_OPENAI_COMPAT_DOC`
+  - `DAILY_AUDIT_YYYY-MM-DD`
+  - `DIFF_HASH_<MASKED>`
+
+---
+
+## 7) 감사로그(append-only) 예시
+
+```json
+{
+  "date": "2026-02-14",
+  "actor": "Cursor",
+  "queue_state_from": "work",
+  "queue_state_to": "work",
+  "decision": "PR_ONLY",
+  "gate_results": {
+    "G0_STOP": "PASS",
+    "G1_DAILY_AUDIT": "UNKNOWN",
+    "G2_PATCH_SIZE": "PASS",
+    "G3_FILE_SAFETY": "PASS",
+    "G4_ALLOWLIST": "UNKNOWN",
+    "G5_SECRETS": "PASS",
+    "G6_APPEND_ONLY": "PASS",
+    "REMOTE_GATE": "UNKNOWN"
+  },
+  "evidence_refs": ["DAILY_AUDIT_2026-02-14", "DIFF_HASH_<MASKED>"],
+  "masked_notes": "added=0.00; deleted=0.00; allowlist_write=UNKNOWN"
+}
+```
+
diff --git a/.cursor/commands/queue-decide.md b/.cursor/commands/queue-decide.md
new file mode 100644
index 0000000..1f2a42c
--- /dev/null
+++ b/.cursor/commands/queue-decide.md
@@ -0,0 +1,223 @@
+# /queue:decide
+AUTO_MERGE/PR_ONLY/ZERO_STOP 결정
+
+Status: active  
+Timezone: Asia/Dubai  
+Scope: 문서/설정 텍스트만(구현/실행/배포 금지)  
+
+---
+
+## 0) 목적
+
+- `/queue:run-gates` 결과를 입력으로 받아 Decision을 고정한다.
+- Decision은 다음 3종만 허용한다:
+  - `AUTO_MERGE`
+  - `PR_ONLY`
+  - `ZERO_STOP`
+
+---
+
+## 1) 입력(Inputs)
+
+| Item | Value |
+|---|---|
+| JOB_ID | `<JOB_ID>` |
+| gate_results | `work/<JOB_ID>/gate_results.json` |
+| Remote Gate 상태 | CONFIRMED/UNKNOWN |
+
+---
+
+## 2) 결정 규칙(요약)
+
+### 2.1 ZERO_STOP (STOP 우선)
+아래 중 1.00개라도 해당하면 `ZERO_STOP`:
+- G0_STOP = FAIL
+- G4_ALLOWLIST = FAIL
+- G5_SECRETS = FAIL
+- G6_APPEND_ONLY = FAIL
+
+### 2.2 AUTO_MERGE (저위험 자동머지)
+아래 모두 PASS이고, Remote Gate가 **CONFIRMED+PASS**일 때만:
+- G0 STOP PASS
+- G1 Daily audit PASS
+- G2 Patch size PASS(≤300.00)
+- G3 File safety PASS(삭제/dep/lock/이진 0.00)
+- G4 Allowlist PASS
+- G5 Secrets PASS
+- G6 Append-only PASS
+- REMOTE_GATE PASS (UNKNOWN이면 PASS로 간주 금지)
+
+### 2.3 PR_ONLY (기본)
+ZERO_STOP가 아니고, AUTO_MERGE 조건을 만족하지 못하면 `PR_ONLY`.
+- 특히 INPUT REQUIRED(브랜치/체크/allowlist_write)가 UNKNOWN이면, AUTO_MERGE로 승격 금지.
+
+---
+
+## 3) 산출물(Outputs)
+
+| Output | Path | Notes |
+|---|---|---|
+| DECISION | `work/<JOB_ID>/DECISION.md` | 고정 포맷 |
+| 감사로그 | `.autodev_queue/audit/audit_log_YYYY-MM-DD.jsonl` | append-only |
+
+---
+
+## 4) DECISION.md 템플릿(고정)
+
+```md
+# DECISION — <JOB_ID>
+
+Decision: PR_ONLY
+
+## Gate Summary
+- G0_STOP: PASS
+- G1_DAILY_AUDIT: UNKNOWN
+- G2_PATCH_SIZE: PASS (added=0.00, deleted=0.00)
+- G3_FILE_SAFETY: PASS
+- G4_ALLOWLIST: UNKNOWN
+- G5_SECRETS: PASS
+- G6_APPEND_ONLY: PASS
+- REMOTE_GATE: UNKNOWN
+
+## Why
+- INPUT REQUIRED가 UNKNOWN이므로 AUTO_MERGE 금지
+
+## Next
+- PR 생성 후 리뷰/체크 통과 시 merge (조건/승인 기반)
+```
+
+---
+
+## 5) 감사로그 예시
+
+```json
+{
+  "date": "2026-02-14",
+  "actor": "Cursor",
+  "queue_state_from": "work",
+  "queue_state_to": "pr",
+  "decision": "PR_ONLY",
+  "gate_results": {
+    "G0_STOP": "PASS",
+    "G1_DAILY_AUDIT": "UNKNOWN",
+    "G2_PATCH_SIZE": "PASS",
+    "G3_FILE_SAFETY": "PASS",
+    "G4_ALLOWLIST": "UNKNOWN",
+    "G5_SECRETS": "PASS",
+    "G6_APPEND_ONLY": "PASS",
+    "REMOTE_GATE": "UNKNOWN"
+  },
+  "evidence_refs": ["DECISION_DOC_CREATED", "GATE_RESULTS_RECORDED"],
+  "masked_notes": "decision=PR_ONLY; reason=UNKNOWN_inputs"
+}
+```
+
diff --git a/.cursor/commands/queue-pr-merge.md b/.cursor/commands/queue-pr-merge.md
new file mode 100644
index 0000000..b4e6b5d
--- /dev/null
+++ b/.cursor/commands/queue-pr-merge.md
@@ -0,0 +1,300 @@
+# /queue:pr-merge
+PR 생성/상태체크/merge(조건/승인 기반)
+
+Status: active  
+Timezone: Asia/Dubai  
+Scope: 문서/설정 텍스트만(구현/실행/배포 금지)  
+
+---
+
+## 0) 목적
+
+- Decision(`AUTO_MERGE/PR_ONLY/ZERO_STOP`)에 따라 PR 생성/상태체크/머지 흐름을 고정한다.
+- Protected branch + Required status checks는 **CONFIRMED/UNKNOWN**으로 분리하고,
+  UNKNOWN이면 “자동 머지” 근거로 사용하지 않는다.
+
+---
+
+## 1) INPUT REQUIRED (없으면 UNKNOWN 유지)
+
+| Item | Value |
+|---|---|
+| 기본 브랜치명 | UNKNOWN |
+| Required status checks 목록 | UNKNOWN |
+| Protected branch 사용 여부 | UNKNOWN |
+
+---
+
+## 2) 입력(Inputs)
+
+| Item | Value |
+|---|---|
+| JOB_ID | `<JOB_ID>` |
+| Decision | `work/<JOB_ID>/DECISION.md` |
+| Patch | `<DIFF_REF>` |
+| Gate Results | `work/<JOB_ID>/GATES.md` |
+
+---
+
+## 3) 절차(Decision별)
+
+### 3.1 ZERO_STOP
+1. PR 생성 금지  
+2. 작업 폴더를 `blocked/`로 격리  
+3. 감사로그 기록(사유/위험/다음조치)  
+4. 복구는 `/incident:recover`로만 진행
+
+### 3.2 PR_ONLY (기본)
+1. PR 생성(승인 기반)
+2. Required status checks 대기
+3. 리뷰 승인(Owner/Operator 정책에 따름)
+4. 모든 조건 충족 시 merge(수동 또는 Cursor에 의해)
+
+주의:
+- Required checks가 UNKNOWN이면 “체크 충족” 판정이 불가하므로,
+  merge는 Operator 승인(근거 기록) 없이는 수행하지 않는다.
+
+### 3.3 AUTO_MERGE (저위험)
+AUTO_MERGE는 아래가 **CONFIRMED**일 때만 수행한다:
+- Protected branch 사용 = CONFIRMED
+- Required status checks 목록 = CONFIRMED
+- 해당 checks 상태 = PASS(허용 상태: successful/skipped/neutral)
+
+CONFIRMED가 아니면 AUTO_MERGE를 PR_ONLY로 강등한다.
+
+---
+
+## 4) 산출물(Outputs)
+
+| Output | Path | Notes |
+|---|---|---|
+| PR 기록 | `pr/<JOB_ID>/PR.md` | 링크 원문 금지 |
+| Merge 기록 | `done/<JOB_ID>/MERGE.md` | 링크 원문 금지 |
+| 감사로그 | `.autodev_queue/audit/audit_log_YYYY-MM-DD.jsonl` | append-only |
+
+---
+
+## 5) PR.md 템플릿(권장)
+
+```md
+# PR — <JOB_ID>
+
+## Decision
+- PR_ONLY
+
+## Branch
+- base_branch: UNKNOWN
+
+## Status Checks
+- required_checks: UNKNOWN
+- check_state: UNKNOWN
+
+## Evidence Refs (원문 링크 금지)
+- PR_REF: PR_<MASKED>
+- CHECKS_REF: CI_<MASKED>
+```
+
+---
+
+## 6) Merge 조건 체크리스트(고정)
+
+| Item | Required | Status |
+|---|---:|---|
+| STOP 없음 | YES | UNKNOWN |
+| Gate G0~G6 재확인 | YES | UNKNOWN |
+| Required checks PASS | YES | UNKNOWN |
+| allowlist 위반 0.00 | YES | UNKNOWN |
+| 삭제/dep/lock/이진 0.00 | YES | UNKNOWN |
+| 민감정보 원문 0.00 | YES | UNKNOWN |
+
+UNKNOWN이 1.00개라도 있으면 AUTO_MERGE 금지(=PR_ONLY 경로 유지).
+
+---
+
+## 7) 감사로그 예시(merge 단계)
+
+```json
+{
+  "date": "2026-02-14",
+  "actor": "Cursor",
+  "queue_state_from": "pr",
+  "queue_state_to": "done",
+  "decision": "AUTO_MERGE",
+  "gate_results": {
+    "G0_STOP": "PASS",
+    "G1_DAILY_AUDIT": "PASS",
+    "G2_PATCH_SIZE": "PASS",
+    "G3_FILE_SAFETY": "PASS",
+    "G4_ALLOWLIST": "PASS",
+    "G5_SECRETS": "PASS",
+    "G6_APPEND_ONLY": "PASS",
+    "REMOTE_GATE": "PASS"
+  },
+  "evidence_refs": ["PR_CREATED", "STATUS_CHECKS_PASS", "MERGE_COMPLETED"],
+  "masked_notes": "pr_ref=<MASKED>"
+}
+```
+
diff --git a/.cursor/commands/incident-recover.md b/.cursor/commands/incident-recover.md
new file mode 100644
index 0000000..d6d7a31
--- /dev/null
+++ b/.cursor/commands/incident-recover.md
@@ -0,0 +1,327 @@
+# /incident:recover
+Incident 복구 체크리스트 생성
+
+Status: active  
+Timezone: Asia/Dubai  
+Scope: 문서/설정 텍스트만(구현/실행/배포 금지)  
+
+---
+
+## 0) 목적
+
+- STOP/게이트 실패/충돌/감사로그 문제 등 “사고(Incident)” 발생 시,
+  **복구 절차를 1장 체크리스트**로 생성하여 재발/확산을 차단한다.
+- 외부 전송(WebChat/메일/업로드)은 기본 차단이며, 필요 시 텍스트-only + `<MASKED>` + Operator 승인.
+
+---
+
+## 1) Incident 유형(분류)
+
+| Type | Example | 기본 Decision |
+|---|---|---|
+| STOP | `.autodev_queue/STOP` 생성 | ZERO_STOP |
+| Allowlist 위반 | 허용 경로 밖 변경 시도 | ZERO_STOP |
+| Secrets 노출 | 토큰/키/내부 URL/실경로 원문 | ZERO_STOP |
+| Claim 충돌 | 동일 JOB_ID 중복 점유 | PR_ONLY(조사) |
+| Gate 실패 | G2/G3/G1 미충족 | PR_ONLY 또는 ZERO_STOP |
+| Audit 위반 | append-only 위반 의심 | ZERO_STOP |
+
+---
+
+## 2) 즉시 조치(Containment) — 10분 체크
+
+1. **STOP 확인**
+   - STOP 존재 시: 모든 작업 중단(우선)
+2. **작업 격리**
+   - 영향을 받는 JOB 폴더를 `blocked/`로 이동(절차에 따라)
+3. **증빙 보존**
+   - diff, gate_results, decision, audit log를 그대로 보존(수정 금지)
+4. **민감정보 마스킹**
+   - 노출이 의심되면 `<MASKED>`로 치환한 “사본 보고서”만 작성(원본 변경 금지)
+
+---
+
+## 3) 복구 절차(Recovery) — 단계별
+
+### 3.1 사건 요약(필수)
+- Incident_ID: `INC_YYYY-MM-DD_<MASKED>`
+- 발생 일시: `YYYY-MM-DD`
+- 범위: affected JOB_ID 목록
+- 트리거: STOP/Allowlist/Secrets/Audit/Conflict 중 1.00개
+- 현재 상태: inbox/claimed/work/pr/done/blocked
+
+### 3.2 원인 추적(정책 기반)
+- Gate 결과(G0~G6)에서 FAIL/UNKNOWN 구간을 확인
+- Decision 기록(DECISION.md)과 불일치 여부 확인
+- audit_log의 append-only 위반 여부 확인
+
+### 3.3 복구 액션(선택)
+
+| Case | Action |
+|---|---|
+| STOP | Operator 승인으로 STOP 해제 후 `blocked→inbox` 재개 |
+| Allowlist 위반 | 위반 변경 폐기 + 스코프 재정의(Plan 재작성) |
+| Secrets 노출 | 노출 범위 최소화 + `<MASKED>` 보고서 작성 + 재발 방지(TOOL_POLICY 강화) |
+| Claim 충돌 | 단일 claimant만 유지, 나머지는 `blocked/` 격리 |
+| Audit 위반 | 로그 원본 보존 + “새 로그 파일로 이어쓰기”(원본 수정 금지) |
+
+---
+
+## 4) 산출물(Outputs)
+
+| Output | Path | Notes |
+|---|---|---|
+| Incident Report | `.autodev_queue/audit/incident_report_YYYY-MM-DD_<MASKED>.md` | 텍스트-only |
+| Recovery Checklist | `.autodev_queue/audit/incident_recover_YYYY-MM-DD_<MASKED>.md` | 1장 |
+| 감사로그 | `.autodev_queue/audit/audit_log_YYYY-MM-DD.jsonl` | append-only |
+
+---
+
+## 5) Incident Report 템플릿(고정)
+
+```md
+# INCIDENT REPORT — INC_YYYY-MM-DD_<MASKED>
+
+## A) Summary
+- Date: YYYY-MM-DD
+- Type: STOP / ALLOWLIST / SECRETS / AUDIT / CONFLICT / GATE_FAIL
+- Affected: <JOB_ID list>
+- Decision: ZERO_STOP
+
+## B) What Happened
+- Trigger:
+- First Detection:
+- Scope:
+
+## C) Gates Snapshot
+- G0_STOP:
+- G1_DAILY_AUDIT:
+- G2_PATCH_SIZE:
+- G3_FILE_SAFETY:
+- G4_ALLOWLIST:
+- G5_SECRETS:
+- G6_APPEND_ONLY:
+- REMOTE_GATE:
+
+## D) Containment
+- blocked isolation:
+- evidence preserved:
+
+## E) Recovery Plan
+- next steps:
+- owner: Operator/Cursor
+- criteria to resume:
+
+## F) Prevention
+- policy changes:
+- additional checks:
+
+## Evidence Refs (원문 링크 금지)
+- <EVIDENCE_KEY list>
+```
+
+---
+
+## 6) 재개 조건(Resume Criteria)
+
+다음이 모두 충족되어야 `blocked→inbox` 재개 가능:
+
+| Item | Required |
+|---|---:|
+| STOP 해제(존재 시) | YES |
+| allowlist 위반 0.00 | YES |
+| secrets 원문 0.00 | YES |
+| audit append-only 정상 | YES |
+| Plan/Decision 재작성 완료 | YES |
+
+UNKNOWN이 1.00개라도 남으면 PR_ONLY로만 재개한다.
