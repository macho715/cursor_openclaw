# /queue:request-patch-draft
OpenClaw에게 patch 제안 생성 요청(제안만)

Status: active  
Timezone: Asia/Dubai  
Stage: 3.00 (Cursor Project Setting)  
Scope: 문서/설정 텍스트만 (구현/실행/배포 금지)  

---

## 0) 목적

- OpenClaw(Worker)에게 **유니파이드 diff “제안”만** 생성하도록 요청한다.
- OpenClaw는 apply/commit/merge 권한이 없고, 결과는 `/queue:run-gates`로 **반드시 검증**된다.

---

## 1) 입력(Inputs)

| Item | Value |
|---|---|
| JOB_ID | `<JOB_ID>` |
| PLAN | `claimed/<JOB_ID>/PLAN.md` |
| Policy SSOT | `docs/policy/*` + `.cursor/rules/AUTODEV_POLICY.md` |
| allowlist_write | UNKNOWN |

---

## 2) Sanitization(필수) — OpenClaw 전달 전

다음은 OpenClaw에 전달하기 전에 반드시 수행:
- 토큰/키/내부 URL/실경로 원문 → `<MASKED>`
- PII(이메일/전화/주소 등) → `<MASKED>`
- Evidence는 “식별자”로만(원문 링크 금지)
- INPUT REQUIRED 미입력 항목은 **UNKNOWN 유지**(가정 금지)

---

## 3) OpenClaw 요청 템플릿(복붙용, 실행 지시 아님)

```md
ROLE
- 너는 OpenClaw(Worker)다. diff/patch "제안"만 가능하다. apply/commit/merge 금지.

SSOT
- Queue: .autodev_queue (inbox→claimed→work→pr→done/blocked)
- Policy: docs/policy/*, .cursor/rules/AUTODEV_POLICY.md
- Job: <JOB_ID>

TASK
- 아래 요구를 만족하는 patch-only(유니파이드 diff)만 출력하라.
- 신규 파일은 --- /dev/null 형태로 생성 diff를 내라.

HARD CONSTRAINT
- 코드 구현/실행/배포 금지
- 파일 삭제 0.00, dep/lockfile 변경 0.00, 이진 변경 0.00
- allowlist_write=UNKNOWN이면: docs/policy/** 및 .cursor/** 외 변경 금지
- 민감정보 원문(토큰/키/내부 URL/실경로) 금지: 발견 시 <MASKED>
- diff 외 텍스트(요약/설명/명령) 출력 금지
- 라인(추가+삭제) 300.00 초과 가능성 있으면, 변경을 최소화해서 300.00 이내로 유지

INPUTS
- PLAN.md:
  <붙여넣기: claimed/<JOB_ID>/PLAN.md>
```

---

## 4) 기대 출력(Outputs)

OpenClaw 출력 허용 범위:
- 유니파이드 diff 단독
- diff 외 텍스트 0.00

---

## 5) 실패 처리

| Failure | Rule | Next |
|---|---|---|
| diff 외 문장 포함 | 계약 위반 | 결과 폐기 + 재요청 |
| 삭제/dep/lock/이진 변경 포함 | 정책 위반 | Gate에서 FAIL 처리 + PR_ONLY 또는 ZERO_STOP |
| allowlist 밖 변경 | 스코프 오염 | 즉시 ZERO_STOP 후보 |
| 민감정보 원문 포함 | 보안 위반 | 즉시 ZERO_STOP + `<MASKED>`로 정리 후 재요청 |

---

## 6) 감사로그(권장)

OpenClaw 요청 자체도 “증빙 이벤트”로 기록(원문 링크 금지):

```json
{
  "date": "YYYY-MM-DD",
  "actor": "Cursor",
  "queue_state_from": "claimed",
  "queue_state_to": "work",
  "decision": "PR_ONLY",
  "gate_results": {
    "G0_STOP": "PASS",
    "G5_SECRETS": "PASS"
  },
  "evidence_refs": ["OPENCLAW_PATCH_REQUESTED"],
  "masked_notes": "job_id=<MASKED>"
}
```
