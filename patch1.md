diff --git a/.cursor/commands/setup-init.md b/.cursor/commands/setup-init.md
--- a/.cursor/commands/setup-init.md
+++ b/.cursor/commands/setup-init.md
@@ -1,2 +1,223 @@
 # /setup:init
 SSOT 로드 + 큐 템플릿 DRY_RUN/적용 가이드
+
+Status: active  
+Timezone: Asia/Dubai  
+Stage: 3.00 (Cursor Project Setting)  
+Scope: 문서/설정 텍스트만 (구현/실행/배포 금지)  
+
+---
+
+## 0) 목적
+
+- Stage 3(정책/레일)에서 **SSOT + Folder Queue + Daily Audit**가 “작동 가능한 최소 구성”인지 DRY_RUN으로 점검한다.
+- 누락이 있으면 **patch-only(유니파이드 diff)** 로 “생성/보완안”만 제안한다(자동 적용 금지).
+- STOP(킬스위치) 우선, 민감정보 `<MASKED>` 우선, INPUT REQUIRED 미입력은 **UNKNOWN 유지**가 원칙이다.
+
+---
+
+## 1) INPUT REQUIRED (없으면 UNKNOWN 유지, 가정 금지)
+
+| Item | Value |
+|---|---|
+| 기본 브랜치명(main/master 등) | UNKNOWN |
+| Required status checks 목록 | UNKNOWN |
+| allowlist_write 경로 | UNKNOWN |
+
+---
+
+## 2) SSOT(기준 경로)
+
+| Category | SSOT Path |
+|---|---|
+| Manifest | `MANIFEST.json` |
+| Baton | `BATON_CURRENT.md` |
+| Queue Root | `.autodev_queue/` |
+| Daily Ops Template | `.autodev_queue/audit/Daily_GoNoGo_TEMPLATE.md` |
+| Policy SSOT | `docs/policy/CURSOR_RULES.md` / `docs/policy/TOOL_POLICY.md` / `docs/policy/APPROVAL_MATRIX.md` / `docs/policy/AUDIT_LOG_SCHEMA.md` |
+| Cursor Rule Summary | `.cursor/rules/AUTODEV_POLICY.md` |
+
+---
+
+## 3) DRY_RUN 체크리스트(점검만)
+
+### 3.1 STOP 우선
+
+| Check | PASS | FAIL |
+|---|---|---|
+| STOP 존재 여부 | `.autodev_queue/STOP` 미존재 | 즉시 `ZERO_STOP` + 진행 중단 |
+
+### 3.2 Queue 구조 존재(폴더)
+
+아래 폴더 “존재 여부만” 점검한다(빈 폴더는 `.gitkeep` 제안 가능):
+
+| Folder | Required |
+|---|---:|
+| `.autodev_queue/inbox/` | YES |
+| `.autodev_queue/claimed/` | YES |
+| `.autodev_queue/work/` | YES |
+| `.autodev_queue/pr/` | YES |
+| `.autodev_queue/done/` | YES |
+| `.autodev_queue/blocked/` | YES |
+| `.autodev_queue/audit/` | YES |
+
+### 3.3 Daily Go/No-Go 템플릿
+
+| Check | PASS | FAIL |
+|---|---|---|
+| Template 존재 | `Daily_GoNoGo_TEMPLATE.md` 존재 | AUTO_MERGE 불가(최소 PR_ONLY) |
+
+### 3.4 정책 문서 존재
+
+| Policy | Required |
+|---|---:|
+| CURSOR_RULES | YES |
+| TOOL_POLICY | YES |
+| APPROVAL_MATRIX | YES |
+| AUDIT_LOG_SCHEMA | YES |
+| AUTODEV_POLICY (Cursor rules summary) | YES |
+
+### 3.5 민감정보/경로 정책 점검(텍스트-only)
+
+- 토큰/키/내부 URL/실경로 원문은 어떤 문서에도 남기지 않는다 → 발견 시 `<MASKED>` 처리.
+- INPUT REQUIRED 3개(브랜치/체크/allowlist_write)가 UNKNOWN이면 **UNKNOWN 유지**(가정 금지).
+
+---
+
+## 4) APPLY_REQUEST(패치 제안만)
+
+DRY_RUN 결과 누락이 있으면 다음만 수행한다:
+
+1. 누락 항목을 목록화한다(보고서).
+2. **patch-only** 로만 보완안을 제안한다.
+3. 실제 apply/test/commit/merge는 Cursor(Control-Plane)가 **별도 승인 후** 수행한다.
+
+---
+
+## 5) 산출물(Outputs)
+
+| Output | Path | Type |
+|---|---|---|
+| Setup DRY_RUN Report | `.autodev_queue/audit/setup_init_report_YYYY-MM-DD.md` | 텍스트 |
+| Audit Log(권장) | `.autodev_queue/audit/audit_log_YYYY-MM-DD.jsonl` | JSONL(append-only) |
+
+---
+
+## 6) 보고서 템플릿(권장)
+
+```md
+# SETUP_INIT_REPORT — YYYY-MM-DD
+
+## A) INPUT REQUIRED
+- base_branch: UNKNOWN
+- required_status_checks: UNKNOWN
+- allowlist_write: UNKNOWN
+
+## B) STOP
+- stop_present: false
+
+## C) Queue Folders
+- inbox/claimed/work/pr/done/blocked/audit: PASS/FAIL
+
+## D) Policy SSOT
+- docs/policy/*: PASS/FAIL
+- .cursor/rules/AUTODEV_POLICY.md: PASS/FAIL
+
+## E) Decision Hint
+- if any FAIL in STOP/allowlist/secrets: ZERO_STOP
+- else: PR_ONLY (UNKNOWN inputs keep UNKNOWN)
+```
+
+---
+
+## 7) 감사로그(append-only) 예시
+
+```json
+{
+  "date": "YYYY-MM-DD",
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
+  "evidence_refs": ["SETUP_INIT_DRY_RUN"],
+  "masked_notes": "base_branch=UNKNOWN; required_checks=UNKNOWN; allowlist_write=UNKNOWN"
+}
+```
+
+---
+
+## 8) ZERO_STOP 트리거(즉시 중단)
+
+| Trigger | Reason |
+|---|---|
+| STOP 존재 | 킬스위치 우선 |
+| allowlist 위반 감지 | 스코프 오염 |
+| 민감정보 원문 감지 | 보안/NDA 위반 |
+
diff --git a/.cursor/commands/queue-claim.md b/.cursor/commands/queue-claim.md
--- a/.cursor/commands/queue-claim.md
+++ b/.cursor/commands/queue-claim.md
@@ -1,2 +1,238 @@
 # /queue:claim
 inbox→claimed (락/충돌/STOP 체크)
+
+Status: active  
+Timezone: Asia/Dubai  
+Stage: 3.00 (Cursor Project Setting)  
+Scope: 문서/설정 텍스트만 (구현/실행/배포 금지)  
+
+---
+
+## 0) 목적
+
+- `.autodev_queue/inbox/<JOB_ID>/` 작업을 **단일 작업자(Cursor)** 가 점유(Claim)한다.
+- 중복/충돌/STOP 존재를 먼저 검사하고, 위반 시 **STOP 우선**으로 차단한다.
+
+---
+
+## 1) 입력(Inputs)
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
+## 2) DRY_RUN(점검만) — Claim 가능 판정
+
+### 2.1 STOP
+
+| Check | PASS | FAIL |
+|---|---|---|
+| STOP 존재 여부 | STOP 미존재 | 즉시 `ZERO_STOP` |
+
+### 2.2 존재/중복 검사(상태 폴더 전수)
+
+| Location | Expectation |
+|---|---|
+| inbox/<JOB_ID> | 존재(YES) |
+| claimed/<JOB_ID> | 미존재(0.00) |
+| work/<JOB_ID> | 미존재(0.00) |
+| pr/<JOB_ID> | 미존재(0.00) |
+| done/<JOB_ID> | 미존재(0.00) |
+| blocked/<JOB_ID> | 미존재(0.00) *(존재 시 Operator 승인 필요)* |
+
+판정:
+- inbox에 없으면: `PR_ONLY`(요청 재확인)
+- claimed/work/pr에 이미 있으면: `PR_ONLY`(충돌 조사)
+- blocked에 있으면: 기본 `ZERO_STOP`(사유/위험 확인 후 Operator 재개)
+- done에 있으면: 재사용 금지(새 JOB_ID로 재등록)
+
+---
+
+## 3) APPLY_REQUEST(상태 전이) — Cursor 소유
+
+> 본 문서는 “절차 정의”다. 실제 이동/적용은 승인 후 Cursor가 수행한다.
+
+1. `inbox/<JOB_ID>` → `claimed/<JOB_ID>` 로 이동(원자적 이동 우선)  
+2. `claimed/<JOB_ID>/CLAIM.json` 생성(락)  
+3. 감사로그 append-only 기록  
+
+### 3.1 CLAIM.json 템플릿(민감정보 금지)
+
+```json
+{
+  "job_id": "<JOB_ID>",
+  "claimed_on": "YYYY-MM-DD",
+  "actor": "Cursor",
+  "notes": "<MASKED>"
+}
+```
+
+---
+
+## 4) 충돌 처리(필수 규칙)
+
+### 4.1 “스테일 claim” 의심 기준(예시)
+
+> 시간 기준은 환경마다 다르므로 숫자 가정 금지. 아래는 절차만 정의한다.
+
+- claimed 폴더에 있으나:
+  - work/pr로 진행 흔적 없음
+  - audit log에 다음 단계 기록 없음
+
+조치:
- `/incident:recover`로 전환하여 “단일 claimant 복구” 체크리스트 작성
- Operator 승인 전까지 병렬 진행 금지
+
+### 4.2 blocked 발견
+- STOP 또는 ZERO_STOP 이력 가능성이 높으므로:
+  - Operator 승인 없이는 재개 금지
+  - incident report 먼저 작성(텍스트-only)
+
+---
+
+## 5) 산출물(Outputs)
+
+| Output | Path |
+|---|---|
+| Claimed Folder | `.autodev_queue/claimed/<JOB_ID>/` |
+| Claim Lock | `claimed/<JOB_ID>/CLAIM.json` |
+| Audit Log | `.autodev_queue/audit/audit_log_YYYY-MM-DD.jsonl` |
+
+---
+
+## 6) 감사로그(append-only) 예시
+
+```json
+{
+  "date": "YYYY-MM-DD",
+  "actor": "Cursor",
+  "queue_state_from": "inbox",
+  "queue_state_to": "claimed",
+  "decision": "PR_ONLY",
+  "gate_results": {
+    "G0_STOP": "PASS",
+    "G6_APPEND_ONLY": "PASS"
+  },
+  "evidence_refs": ["QUEUE_CLAIM"],
+  "masked_notes": "job_id=<MASKED>"
+}
+```
+
+---
+
+## 7) ZERO_STOP 트리거
+
+| Trigger | Action |
+|---|---|
+| STOP 존재 | 즉시 중단 + blocked 격리(필요 시) |
+| 중복 claim 확정(동시 수정 위험) | PR_ONLY로 강등 + incident 조사 |
+| audit append-only 위반 의심 | 즉시 ZERO_STOP + 원본 보존 |
+
diff --git a/.cursor/commands/queue-open-plan.md b/.cursor/commands/queue-open-plan.md
--- a/.cursor/commands/queue-open-plan.md
+++ b/.cursor/commands/queue-open-plan.md
@@ -1,2 +1,268 @@
 # /queue:open-plan
 S3 Plan 1장 요약 생성(범위/테스트/롤백/리스크)
+
+Status: active  
+Timezone: Asia/Dubai  
+Stage: 3.00 (Cursor Project Setting)  
+Scope: 문서/설정 텍스트만 (구현/실행/배포 금지)  
+
+---
+
+## 0) 목적
+
+- `claimed/<JOB_ID>` 작업에 대해 **1장짜리 PLAN**(스코프/가드/검증/복구)을 고정 포맷으로 만든다.
+- PLAN은 OpenClaw patch 제안의 “입력 계약(SSOT)”이며, 이후 단계에서 **Intent Lock**으로 사용된다.
+
+---
+
+## 1) 입력(Inputs)
+
+| Item | Value |
+|---|---|
+| JOB_ID | `<JOB_ID>` |
+| Queue Path | `.autodev_queue/claimed/<JOB_ID>/` |
+| 기본 브랜치명 | UNKNOWN |
+| Required status checks | UNKNOWN |
+| allowlist_write | UNKNOWN |
+
+---
+
+## 2) 산출 위치(권장)
+
+| File | Path | Purpose |
+|---|---|---|
+| PLAN | `claimed/<JOB_ID>/PLAN.md` | 1장 계획 |
+| INTENT LOCK | `claimed/<JOB_ID>/intent_lock.yml` | “바꾸지 않을 것” 잠금 |
+| EVIDENCE | `claimed/<JOB_ID>/EVIDENCE.md` | 링크 원문 금지(식별자만) |
+
+---
+
+## 3) 작성 절차(DRY_RUN → 문서 작성)
+
+1. STOP 존재 여부 확인(있으면 즉시 중단)  
+2. 요청(REQUEST) 확인  
+   - 요청 텍스트가 없으면, PLAN에 `request=UNKNOWN`으로 남긴다(가정 금지).  
+3. Scope 정의  
+   - allowlist_write가 UNKNOWN이면, Stage 3 범위(정책/커맨드 텍스트)로만 제한:
+     - `docs/policy/**`
+     - `.cursor/**`
+4. Out-of-scope(금지) 고정  
+   - 코드 구현/실행/배포 금지  
+   - 파일 삭제 0.00, dep/lockfile 변경 0.00, 이진 변경 0.00  
+   - 민감정보 원문 금지(`<MASKED>`)  
+5. Validation(검증) 정의  
+   - Gate(G0~G6) 결과표 생성(실행 지시 아님)  
+6. Rollback/Recovery 정의  
+   - 실패 시 blocked 격리 + audit 기록  
+7. Evidence Refs 정리  
+   - 원문 링크/내부 URL 금지, “식별자”만 기록  
+
+---
+
+## 4) PLAN.md 템플릿(고정)
+
+```md
+# PLAN — <JOB_ID>
+
+## A) Request
+- request: UNKNOWN
+
+## B) Scope (허용 변경)
+- allowlist_write: UNKNOWN
+- allowed_paths:
+  - docs/policy/**
+  - .cursor/**
+
+## C) Out of Scope (금지)
+- code_implementation: true
+- execution_or_deploy: true
+- delete_files: 0.00
+- dep_lock_changes: 0.00
+- binary_changes: 0.00
+- secrets_or_internal_urls_raw: 0.00
+
+## D) Deliverables
+- patch-only(유니파이드 diff)로 문서 생성/수정
+- audit append-only 기록
+- outputs:
+  - claimed/<JOB_ID>/PLAN.md
+  - claimed/<JOB_ID>/intent_lock.yml (권장)
+  - work/<JOB_ID>/GATES.md (후속)
+
+## E) Validation (예시, 실행 지시 아님)
+- run_gates:
+  - G0 STOP
+  - G1 Daily Go/No-Go
+  - G2 Patch size ≤ 300.00
+  - G3 File safety(삭제/dep/lock/이진 0.00)
+  - G4 Allowlist
+  - G5 Secrets
+  - G6 Append-only
+- decision: AUTO_MERGE / PR_ONLY / ZERO_STOP
+
+## F) Rollback / Recovery
+- on_fail: decision=ZERO_STOP, move_to=blocked, audit=append
+- resume: Operator 승인 필요
+
+## G) Risks / Gates Focus
+- STOP 우선
+- allowlist_write UNKNOWN이면 AUTO_MERGE 금지
+- secrets 1.00건이라도 즉시 ZERO_STOP
+
+## H) Evidence Refs (원문 링크 금지)
+- REQUEST_REF: <MASKED>
+- POLICY_REF: CURSOR_RULES/TOOL_POLICY/APPROVAL_MATRIX/AUDIT_LOG_SCHEMA
+```
+
+---
+
+## 5) intent_lock.yml 템플릿(권장)
+
+```yml
+job_id: "<JOB_ID>"
+locked:
+  - no_code_implementation
+  - no_execution_or_deploy
+  - no_delete_files
+  - no_dep_lock_changes
+  - no_binary_changes
+  - no_secrets_or_internal_urls_raw
+unknowns:
+  - base_branch
+  - required_status_checks
+  - allowlist_write
+```
+
+---
+
+## 6) EVIDENCE.md 규칙
+
+- URL 원문 금지, 내부 URL/실경로 금지  
+- 아래처럼 “키”만 기록:
+
+```md
+# EVIDENCE — <JOB_ID>
+
+- REQUEST_REF: <MASKED>
+- GH_PROTECTED_BRANCH_DOC
+- OLLAMA_OPENAI_COMPAT_DOC
+- DAILY_AUDIT_YYYY-MM-DD
+```
+
+---
+
+## 7) 산출물(Outputs)
+
+| Output | Path |
+|---|---|
+| PLAN | `.autodev_queue/claimed/<JOB_ID>/PLAN.md` |
+| INTENT LOCK(권장) | `.autodev_queue/claimed/<JOB_ID>/intent_lock.yml` |
+| EVIDENCE(권장) | `.autodev_queue/claimed/<JOB_ID>/EVIDENCE.md` |
+
diff --git a/.cursor/commands/request-patch-draft.md b/.cursor/commands/request-patch-draft.md
--- a/.cursor/commands/request-patch-draft.md
+++ b/.cursor/commands/request-patch-draft.md
@@ -1,2 +1,270 @@
 # /queue:request-patch-draft
 OpenClaw에게 patch 제안 생성 요청(제안만)
+
+Status: active  
+Timezone: Asia/Dubai  
+Stage: 3.00 (Cursor Project Setting)  
+Scope: 문서/설정 텍스트만 (구현/실행/배포 금지)  
+
+---
+
+## 0) 목적
+
+- OpenClaw(Worker)에게 **유니파이드 diff “제안”만** 생성하도록 요청한다.
+- OpenClaw는 apply/commit/merge 권한이 없고, 결과는 `/queue:run-gates`로 **반드시 검증**된다.
+
+---
+
+## 1) 입력(Inputs)
+
+| Item | Value |
+|---|---|
+| JOB_ID | `<JOB_ID>` |
+| PLAN | `claimed/<JOB_ID>/PLAN.md` |
+| Policy SSOT | `docs/policy/*` + `.cursor/rules/AUTODEV_POLICY.md` |
+| allowlist_write | UNKNOWN |
+
+---
+
+## 2) Sanitization(필수) — OpenClaw 전달 전
+
+다음은 OpenClaw에 전달하기 전에 반드시 수행:
+- 토큰/키/내부 URL/실경로 원문 → `<MASKED>`
+- PII(이메일/전화/주소 등) → `<MASKED>`
+- Evidence는 “식별자”로만(원문 링크 금지)
+- INPUT REQUIRED 미입력 항목은 **UNKNOWN 유지**(가정 금지)
+
+---
+
+## 3) OpenClaw 요청 템플릿(복붙용, 실행 지시 아님)
+
+```md
+ROLE
+- 너는 OpenClaw(Worker)다. diff/patch "제안"만 가능하다. apply/commit/merge 금지.
+
+SSOT
+- Queue: .autodev_queue (inbox→claimed→work→pr→done/blocked)
+- Policy: docs/policy/*, .cursor/rules/AUTODEV_POLICY.md
+- Job: <JOB_ID>
+
+TASK
+- 아래 요구를 만족하는 patch-only(유니파이드 diff)만 출력하라.
+- 신규 파일은 --- /dev/null 형태로 생성 diff를 내라.
+
+HARD CONSTRAINT
+- 코드 구현/실행/배포 금지
+- 파일 삭제 0.00, dep/lockfile 변경 0.00, 이진 변경 0.00
+- allowlist_write=UNKNOWN이면: docs/policy/** 및 .cursor/** 외 변경 금지
+- 민감정보 원문(토큰/키/내부 URL/실경로) 금지: 발견 시 <MASKED>
+- diff 외 텍스트(요약/설명/명령) 출력 금지
+- 라인(추가+삭제) 300.00 초과 가능성 있으면, 변경을 최소화해서 300.00 이내로 유지
+
+INPUTS
+- PLAN.md:
+  <붙여넣기: claimed/<JOB_ID>/PLAN.md>
+```
+
+---
+
+## 4) 기대 출력(Outputs)
+
+OpenClaw 출력 허용 범위:
+- 유니파이드 diff 단독
+- diff 외 텍스트 0.00
+
+---
+
+## 5) 실패 처리
+
+| Failure | Rule | Next |
+|---|---|---|
+| diff 외 문장 포함 | 계약 위반 | 결과 폐기 + 재요청 |
+| 삭제/dep/lock/이진 변경 포함 | 정책 위반 | Gate에서 FAIL 처리 + PR_ONLY 또는 ZERO_STOP |
+| allowlist 밖 변경 | 스코프 오염 | 즉시 ZERO_STOP 후보 |
+| 민감정보 원문 포함 | 보안 위반 | 즉시 ZERO_STOP + `<MASKED>`로 정리 후 재요청 |
+
+---
+
+## 6) 감사로그(권장)
+
+OpenClaw 요청 자체도 “증빙 이벤트”로 기록(원문 링크 금지):
+
+```json
+{
+  "date": "YYYY-MM-DD",
+  "actor": "Cursor",
+  "queue_state_from": "claimed",
+  "queue_state_to": "work",
+  "decision": "PR_ONLY",
+  "gate_results": {
+    "G0_STOP": "PASS",
+    "G5_SECRETS": "PASS"
+  },
+  "evidence_refs": ["OPENCLAW_PATCH_REQUESTED"],
+  "masked_notes": "job_id=<MASKED>"
+}
+```
+
diff --git a/.cursor/commands/queue-run-gates.md b/.cursor/commands/queue-run-gates.md
--- a/.cursor/commands/queue-run-gates.md
+++ b/.cursor/commands/queue-run-gates.md
@@ -1,2 +1,341 @@
 # /queue:run-gates
 G0~G6 실행 + Evidence 수집
+
+Status: active  
+Timezone: Asia/Dubai  
+Stage: 3.00 (Cursor Project Setting)  
+Scope: 문서/설정 텍스트만 (구현/실행/배포 금지)  
+
+---
+
+## 0) 목적
+
+- 제안된 diff(패치)를 **Gate(G0~G6)** 로 평가하여 `PASS/FAIL/UNKNOWN`을 산출한다.
+- 결과는 `/queue:decide`의 입력이며, UNKNOWN이 남으면 AUTO_MERGE 승격을 금지한다.
+
+---
+
+## 1) 입력(Inputs)
+
+| Item | Value |
+|---|---|
+| JOB_ID | `<JOB_ID>` |
+| Patch(diff) | `<DIFF_REF>` |
+| 오늘 Daily audit=Go | UNKNOWN |
+| allowlist_write | UNKNOWN |
+| Required status checks | UNKNOWN |
+
+---
+
+## 2) Gate 정의(고정)
+
+| Gate | Name | PASS 조건 | FAIL 시 |
+|---|---|---|---|
+| G0 | STOP | STOP 미존재 | ZERO_STOP |
+| G1 | Daily Go/No-Go | 오늘 audit=Go | AUTO_MERGE 금지(PR_ONLY) |
+| G2 | Patch Size | added+deleted ≤ 300.00 | AUTO_MERGE 금지(PR_ONLY) |
+| G3 | File Safety | 삭제 0.00 / dep·lock 0.00 / 이진 0.00 | PR_ONLY 또는 ZERO_STOP |
+| G4 | Allowlist | allowlist_write 내부만 | ZERO_STOP |
+| G5 | Secrets/NDA | 민감정보 원문 0.00 | ZERO_STOP |
+| G6 | Append-only | 감사로그 append-only | ZERO_STOP |
+
+REMOTE_GATE(별도 기록):
+- Protected branch / Required checks 상태는 **CONFIRMED/UNKNOWN** 분리 기록
+- UNKNOWN이면 AUTO_MERGE에서 PASS로 간주 금지
+
+---
+
+## 3) DRY_RUN 평가 절차(점검만)
+
+1. G0 STOP: `.autodev_queue/STOP` 존재 여부  
+2. G1 Daily audit:
+   - 오늘자 audit 파일 존재/결과(Go/No-Go) 확인
+   - 없으면 `UNKNOWN`
+3. G2 Patch size:
+   - diff에서 `+`/`-` 라인 수를 산출하여 2.00자리로 기록
+4. G3 File safety:
+   - 파일 삭제 여부
+   - dep/lockfile 변경 여부
+   - 이진 변경 여부(추정 금지: “탐지 기준”을 Evidence로 남김)
+5. G4 Allowlist:
+   - allowlist_write가 UNKNOWN이면 허용 경로를 Stage 3 텍스트 범위로 제한:
+     - `docs/policy/**`
+     - `.cursor/**`
+6. G5 Secrets:
+   - 토큰/키/내부 URL/실경로 원문 탐지 시 FAIL
+7. G6 Append-only:
+   - audit log 파일에 “기존 라인 수정/삭제” 흔적이 있는지 확인(원본 보존)
+8. REMOTE_GATE:
+   - 설정이 확인되지 않으면 `UNKNOWN`
+
+---
+
+## 4) 산출물(Outputs)
+
+| Output | Path | Notes |
+|---|---|---|
+| Gate 결과표 | `work/<JOB_ID>/GATES.md` | 표 1개로 고정 |
+| Gate 결과 JSON | `work/<JOB_ID>/gate_results.json` | 권장 |
+| Evidence | `work/<JOB_ID>/EVIDENCE.md` | 원문 링크 금지 |
+| Audit Log | `.autodev_queue/audit/audit_log_YYYY-MM-DD.jsonl` | append-only |
+
+---
+
+## 5) GATES.md 포맷(고정)
+
+```md
+# GATES — <JOB_ID>
+
+| Gate | Result | Metric/Note |
+|---|---|---|
+| G0_STOP | PASS/FAIL | stop_present=false |
+| G1_DAILY_AUDIT | PASS/FAIL/UNKNOWN | daily=Go? |
+| G2_PATCH_SIZE | PASS/FAIL | added=0.00, deleted=0.00, total=0.00 |
+| G3_FILE_SAFETY | PASS/FAIL | del=0.00, dep_lock=0.00, bin=0.00 |
+| G4_ALLOWLIST | PASS/FAIL/UNKNOWN | allowlist_write=UNKNOWN |
+| G5_SECRETS | PASS/FAIL | secrets_raw=0.00 |
+| G6_APPEND_ONLY | PASS/FAIL | append_only=true |
+| REMOTE_GATE | PASS/FAIL/UNKNOWN | protected=UNKNOWN, checks=UNKNOWN |
+```
+
+---
+
+## 6) gate_results.json(권장 구조)
+
+```json
+{
+  "job_id": "<JOB_ID>",
+  "date": "YYYY-MM-DD",
+  "metrics": {
+    "lines_added": 0.00,
+    "lines_deleted": 0.00,
+    "lines_total": 0.00,
+    "files_deleted": 0.00,
+    "dep_lock_changes": 0.00,
+    "binary_changes": 0.00,
+    "secrets_raw": 0.00
+  },
+  "gates": {
+    "G0_STOP": "PASS",
+    "G1_DAILY_AUDIT": "UNKNOWN",
+    "G2_PATCH_SIZE": "PASS",
+    "G3_FILE_SAFETY": "PASS",
+    "G4_ALLOWLIST": "UNKNOWN",
+    "G5_SECRETS": "PASS",
+    "G6_APPEND_ONLY": "PASS",
+    "REMOTE_GATE": "UNKNOWN"
+  }
+}
+```
+
+---
+
+## 7) Evidence 규칙(원문 링크 금지)
+
+EVIDENCE.md에는 “키”만 기록한다:
+
+```md
+# EVIDENCE — <JOB_ID>
+
+- DIFF_REF: DIFF_<MASKED>
+- DAILY_AUDIT: DAILY_AUDIT_YYYY-MM-DD
+- POLICY: CURSOR_RULES / TOOL_POLICY / APPROVAL_MATRIX / AUDIT_LOG_SCHEMA
+- REMOTE_GATE_STATUS: UNKNOWN
+```
+
+---
+
+## 8) No-Go 우선순위
+
+| Condition | Decision |
+|---|---|
+| G0/G4/G5/G6 중 1.00개라도 FAIL | ZERO_STOP |
+| 그 외 FAIL 또는 UNKNOWN 존재 | PR_ONLY |
+| ALL PASS + REMOTE_GATE PASS(CONFIRMED) | AUTO_MERGE 후보 |
+
diff --git a/.cursor/commands/queue-decide.md b/.cursor/commands/queue-decide.md
--- a/.cursor/commands/queue-decide.md
+++ b/.cursor/commands/queue-decide.md
@@ -1,2 +1,253 @@
 # /queue:decide
 AUTO_MERGE/PR_ONLY/ZERO_STOP 결정
+
+Status: active  
+Timezone: Asia/Dubai  
+Stage: 3.00 (Cursor Project Setting)  
+Scope: 문서/설정 텍스트만 (구현/실행/배포 금지)  
+
+---
+
+## 0) 목적
+
+- `/queue:run-gates` 결과를 입력으로 **Decision을 3종으로만 고정**한다:
+  - `AUTO_MERGE`
+  - `PR_ONLY`
+  - `ZERO_STOP`
+- UNKNOWN이 남아있으면 AUTO_MERGE로 승격하지 않는다(가정 금지).
+
+---
+
+## 1) 입력(Inputs)
+
+| Item | Value |
+|---|---|
+| JOB_ID | `<JOB_ID>` |
+| gate_results | `work/<JOB_ID>/gate_results.json` |
+| GATES.md | `work/<JOB_ID>/GATES.md` |
+| INPUT REQUIRED (브랜치/체크/allowlist_write) | UNKNOWN |
+
+---
+
+## 2) 결정 규칙(고정)
+
+### 2.1 ZERO_STOP (STOP 우선)
+아래 중 1.00개라도 충족 시 `ZERO_STOP`:
+- G0_STOP = FAIL
+- G4_ALLOWLIST = FAIL
+- G5_SECRETS = FAIL
+- G6_APPEND_ONLY = FAIL
+
+### 2.2 AUTO_MERGE (저위험 자동머지)
+아래 모두 PASS이고, REMOTE_GATE가 **PASS(CONFIRMED)** 일 때만:
+- G0 PASS
+- G1 PASS
+- G2 PASS (≤300.00)
+- G3 PASS (삭제/dep·lock/이진 0.00)
+- G4 PASS
+- G5 PASS
+- G6 PASS
+- REMOTE_GATE PASS
+- INPUT REQUIRED 3개가 모두 CONFIRMED(UNKNOWN이면 금지)
+
+### 2.3 PR_ONLY (기본)
+ZERO_STOP가 아니고, AUTO_MERGE 조건을 만족하지 못하면 `PR_ONLY`.
+- 특히 `REMOTE_GATE=UNKNOWN` 또는 INPUT REQUIRED가 UNKNOWN이면 PR_ONLY 고정.
+
+---
+
+## 3) 산출물(Outputs)
+
+| Output | Path |
+|---|---|
+| DECISION | `work/<JOB_ID>/DECISION.md` |
+| Audit Log | `.autodev_queue/audit/audit_log_YYYY-MM-DD.jsonl` |
+
+---
+
+## 4) DECISION.md 템플릿(고정)
+
+```md
+# DECISION — <JOB_ID>
+
+Decision: PR_ONLY
+Date: YYYY-MM-DD
+
+## Gate Summary
+- G0_STOP: PASS
+- G1_DAILY_AUDIT: UNKNOWN
+- G2_PATCH_SIZE: PASS (added=0.00, deleted=0.00, total=0.00)
+- G3_FILE_SAFETY: PASS (del=0.00, dep_lock=0.00, bin=0.00)
+- G4_ALLOWLIST: UNKNOWN
+- G5_SECRETS: PASS
+- G6_APPEND_ONLY: PASS
+- REMOTE_GATE: UNKNOWN
+
+## Why
+- UNKNOWN 존재(REMOTE/INPUT REQUIRED 포함) → AUTO_MERGE 승격 금지
+
+## Next
+- /queue:pr-merge (PR_ONLY 경로)
+```
+
+---
+
+## 5) 감사로그(append-only) 예시
+
+```json
+{
+  "date": "YYYY-MM-DD",
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
+  "evidence_refs": ["DECISION_CREATED"],
+  "masked_notes": "job_id=<MASKED>"
+}
+```
+
diff --git a/.cursor/commands/queue-pr-merge.md b/.cursor/commands/queue-pr-merge.md
--- a/.cursor/commands/queue-pr-merge.md
+++ b/.cursor/commands/queue-pr-merge.md
@@ -1,2 +1,340 @@
 # /queue:pr-merge
 PR 생성/상태체크/merge(조건/승인 기반)
+
+Status: active  
+Timezone: Asia/Dubai  
+Stage: 3.00 (Cursor Project Setting)  
+Scope: 문서/설정 텍스트만 (구현/실행/배포 금지)  
+
+---
+
+## 0) 목적
+
+- Decision(`AUTO_MERGE/PR_ONLY/ZERO_STOP`)에 따라 PR 생성/체크/머지 절차를 고정한다.
+- Protected branch / Required status checks는 **CONFIRMED/UNKNOWN**으로 분리한다.
+- UNKNOWN이 남으면 AUTO_MERGE는 금지(=PR_ONLY 유지).
+
+---
+
+## 1) INPUT REQUIRED (없으면 UNKNOWN 유지)
+
+| Item | Value |
+|---|---|
+| 기본 브랜치명 | UNKNOWN |
+| Protected branch 사용 여부 | UNKNOWN |
+| Required status checks 목록 | UNKNOWN |
+
+---
+
+## 2) 입력(Inputs)
+
+| Item | Value |
+|---|---|
+| JOB_ID | `<JOB_ID>` |
+| DECISION | `work/<JOB_ID>/DECISION.md` |
+| Gate Results | `work/<JOB_ID>/GATES.md` |
+| Patch(diff) | `<DIFF_REF>` |
+
+---
+
+## 3) Decision별 절차(고정)
+
+### 3.1 ZERO_STOP
+1. PR 생성 금지  
+2. 작업 폴더 `blocked/` 격리  
+3. 감사로그: 사유/위험/다음조치 기록  
+4. 복구는 `/incident:recover`로만 진행
+
+### 3.2 PR_ONLY (기본)
+1. PR 생성(승인 기반)  
+2. 상태체크 대기(Required checks가 UNKNOWN이면, “충족 판정”을 하지 않는다)  
+3. 리뷰 승인(승인 주체는 APPROVAL_MATRIX에 따름)  
+4. 모든 조건이 CONFIRMED일 때만 merge  
+
+### 3.3 AUTO_MERGE (저위험)
+AUTO_MERGE는 아래가 **CONFIRMED**일 때만 수행:
+- Protected branch=CONFIRMED
+- Required status checks 목록=CONFIRMED
+- checks 상태가 PASS(허용 상태: successful/skipped/neutral)
+
+CONFIRMED가 아니면 즉시 PR_ONLY로 강등한다.
+
+---
+
+## 4) 산출물(Outputs)
+
+| Output | Path | Notes |
+|---|---|---|
+| PR 기록 | `pr/<JOB_ID>/PR.md` | 원문 링크 금지 |
+| Merge 기록 | `done/<JOB_ID>/MERGE.md` | 원문 링크 금지 |
+| Post-check | `done/<JOB_ID>/POSTCHECK.md` | 권장 |
+| Audit Log | `.autodev_queue/audit/audit_log_YYYY-MM-DD.jsonl` | append-only |
+
+---
+
+## 5) PR.md 템플릿(고정)
+
+```md
+# PR — <JOB_ID>
+
+Decision: PR_ONLY
+Date: YYYY-MM-DD
+
+## Branch
+- base_branch: UNKNOWN
+
+## Required Checks
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
+## 6) Merge 체크리스트(UNKNOWN 있으면 AUTO_MERGE 금지)
+
+| Item | Required | Status |
+|---|---:|---|
+| STOP 없음 | YES | UNKNOWN |
+| Gate G0~G6 PASS | YES | UNKNOWN |
+| Required checks PASS | YES | UNKNOWN |
+| allowlist 위반 0.00 | YES | UNKNOWN |
+| 삭제/dep·lock/이진 0.00 | YES | UNKNOWN |
+| 민감정보 원문 0.00 | YES | UNKNOWN |
+
+---
+
+## 7) done 산출물 템플릿(권장)
+
+### 7.1 MERGE.md
+
+```md
+# MERGE — <JOB_ID>
+
+Date: YYYY-MM-DD
+Decision: AUTO_MERGE
+
+## Outcome
+- merged: true
+- method: AUTO_MERGE / MANUAL_MERGE
+
+## Evidence Refs (원문 링크 금지)
+- PR_REF: PR_<MASKED>
+- CHECKS_REF: CI_<MASKED>
+- MERGE_REF: MERGE_<MASKED>
+```
+
+### 7.2 POSTCHECK.md
+
+```md
+# POSTCHECK — <JOB_ID>
+
+Date: YYYY-MM-DD
+
+## Checks
+- gates_reconfirmed: PASS/FAIL/UNKNOWN
+- audit_appended: PASS/FAIL
+- artifacts_moved_to_done: PASS/FAIL
+```
+
+---
+
+## 8) 감사로그(append-only) 예시
+
+```json
+{
+  "date": "YYYY-MM-DD",
+  "actor": "Cursor",
+  "queue_state_from": "pr",
+  "queue_state_to": "done",
+  "decision": "PR_ONLY",
+  "gate_results": {
+    "G0_STOP": "PASS",
+    "G1_DAILY_AUDIT": "PASS",
+    "G2_PATCH_SIZE": "PASS",
+    "G3_FILE_SAFETY": "PASS",
+    "G4_ALLOWLIST": "PASS",
+    "G5_SECRETS": "PASS",
+    "G6_APPEND_ONLY": "PASS",
+    "REMOTE_GATE": "UNKNOWN"
+  },
+  "evidence_refs": ["PR_MERGED"],
+  "masked_notes": "job_id=<MASKED>; pr_ref=<MASKED>"
+}
+```
+
diff --git a/.cursor/commands/incident-recover.md b/.cursor/commands/incident-recover.md
--- a/.cursor/commands/incident-recover.md
+++ b/.cursor/commands/incident-recover.md
@@ -1,2 +1,364 @@
 # /incident:recover
 Incident 복구 체크리스트 생성
+
+Status: active  
+Timezone: Asia/Dubai  
+Stage: 3.00 (Cursor Project Setting)  
+Scope: 문서/설정 텍스트만 (구현/실행/배포 금지)  
+
+---
+
+## 0) 목적
+
+- STOP/게이트 실패/충돌/감사로그 위반 등 Incident 발생 시,
+  **확산 차단(Containment) → 원인 추적 → 복구(Recovery) → 재개 조건(Resume)** 을 1장 체크리스트로 고정한다.
+- 외부 전송(WebChat/메일/업로드)은 기본 차단. 예외는 Operator 승인 + 텍스트-only + `<MASKED>`만 허용.
+
+---
+
+## 1) Incident 유형(분류)
+
+| Type | Trigger | Default Decision |
+|---|---|---|
+| STOP | `.autodev_queue/STOP` 존재 | ZERO_STOP |
+| ALLOWLIST | 허용 경로 밖 변경 | ZERO_STOP |
+| SECRETS | 토큰/키/내부 URL/실경로 원문 | ZERO_STOP |
+| AUDIT | append-only 위반 의심 | ZERO_STOP |
+| CONFLICT | JOB_ID 중복 claim/work | PR_ONLY(조사) |
+| GATE_FAIL | G1/G2/G3 FAIL | PR_ONLY 또는 ZERO_STOP |
+
+---
+
+## 2) 즉시 조치(Containment) — 우선순위
+
+1. STOP 확인(존재 시 즉시 중단)  
+2. 영향 JOB 식별(affected JOB_ID 목록화)  
+3. 작업 격리: `blocked/`로 이동(절차에 따라)  
+4. 증빙 보존: diff/gates/decision/audit log 원본을 수정하지 않는다  
+5. 민감정보 노출 의심 시: “사본 보고서”에만 `<MASKED>` 반영(원본 변경 금지)
+
+---
+
+## 3) 복구 절차(Recovery)
+
+### 3.1 사건 요약(필수)
+
+| Field | Value |
+|---|---|
+| Incident_ID | `INC_YYYY-MM-DD_<MASKED>` |
+| Date | `YYYY-MM-DD` |
+| Type | STOP/ALLOWLIST/SECRETS/AUDIT/CONFLICT/GATE_FAIL |
+| Affected JOB_ID | `<JOB_ID list>` |
+| Current Queue State | inbox/claimed/work/pr/done/blocked |
+| Decision | ZERO_STOP / PR_ONLY |
+
+### 3.2 원인 추적(Policy 기반)
+- Gate 결과(G0~G6)에서 FAIL/UNKNOWN 구간 확인
+- DECISION.md와 실제 행동(상태 전이/PR/merge) 불일치 여부 확인
+- audit log append-only 위반 여부 확인(원본 보존)
+
+### 3.3 복구 액션(케이스별)
+
+| Case | Action | Resume Rule |
+|---|---|---|
+| STOP | Operator 승인으로 STOP 해제 후 재개 | STOP 해제 + 기록 필수 |
+| ALLOWLIST | 위반 변경 폐기 + PLAN 스코프 축소 | allowlist 100.00% 준수 |
+| SECRETS | 노출 범위 최소화 + `<MASKED>` 보고서 | secrets_raw=0.00 |
+| AUDIT | 원본 보존 + 새 로그 파일로 이어쓰기 | append-only 회복 |
+| CONFLICT | 단일 claimant만 유지, 나머지 격리 | 중복 0.00 |
+
+---
+
+## 4) 산출물(Outputs)
+
+| Output | Path | Notes |
+|---|---|---|
+| Incident Report | `.autodev_queue/audit/incident_report_YYYY-MM-DD_<MASKED>.md` | 텍스트-only |
+| Recovery Checklist | `.autodev_queue/audit/incident_recover_YYYY-MM-DD_<MASKED>.md` | 1장 |
+| Audit Log | `.autodev_queue/audit/audit_log_YYYY-MM-DD.jsonl` | append-only |
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
+| secrets_raw 0.00 | YES |
+| audit append-only 정상 | YES |
+| PLAN/DECISION 재작성 | YES |
+
+UNKNOWN이 1.00개라도 남으면 PR_ONLY로만 재개한다.
