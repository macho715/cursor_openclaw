# CURSOR_RULES (Policy SSOT) — Option A / Folder Queue

Status: active  
Baton_ID: cursor_setting_policy_lock_v2.0  
Timezone: Asia/Dubai  
Updated: 2026-02-14  
Scope: 정책 문서/설정 텍스트만 (구현/실행/배포 금지)

---

## 0) INPUT REQUIRED (없으면 UNKNOWN)

| Item | Value |
|---|---|
| 기본 브랜치명 | UNKNOWN |
| Required status checks 목록 | UNKNOWN |
| allowlist_write 경로 | UNKNOWN |

---

## 1) ROLE / 권한 경계(불변)

### 1.1 Cursor (Control-Plane)
- APPLY / TEST / COMMIT / PR / MERGE / ROLLBACK **소유**
- Gate 판정 및 Decision(AUTO_MERGE/PR_ONLY/ZERO_STOP) 최종 결정

### 1.2 OpenClaw (Worker)
- diff/patch **제안만**
- 로컬/원격에서 APPLY/COMMIT/MERGE 수행 금지

### 1.3 Operator (Human)
- Repo 설정(Protected branch/Required status checks) **CONFIRMED 처리**
- 예외 승인, STOP 해제, 정책 업데이트 승인

---

## 2) SSOT(변경 금지)

| SSOT | Path / Object |
|---|---|
| Folder Queue | `.autodev_queue/` |
| Daily Ops Template | `.autodev_queue/audit/Daily_GoNoGo_TEMPLATE.md` |
| STOP(킬스위치) | `.autodev_queue/STOP` (존재 유무만) |
| 정책 문서 | `docs/policy/*.md` |
| Cursor 요약 규칙 | `.cursor/rules/AUTODEV_POLICY.md` |

---

## 3) Folder Queue 상태머신(SSOT)

### 3.1 States

| State | Meaning |
|---|---|
| inbox | 신규 작업(폴더 단위) |
| claimed | Cursor가 작업 락(Claim) |
| work | 패치 초안 생성/검증 진행 |
| pr | PR 생성 후 상태 추적 |
| done | merge + post-check 완료 |
| blocked | STOP / ZERO_STOP / 수동 격리 |

### 3.2 Allowed Transitions (허용)

| From | To | Trigger | Actor | Audit Log |
|---|---|---|---|---|
| inbox | claimed | claim 작업 | Cursor | REQUIRED |
| claimed | work | 작업 착수 | Cursor | REQUIRED |
| work | pr | PR 생성(또는 PR_ONLY 결정) | Cursor | REQUIRED |
| pr | done | merge 완료 | Cursor | REQUIRED |
| * | blocked | STOP 감지 또는 ZERO_STOP | Cursor | REQUIRED |
| blocked | inbox | 수동 재개(사유/승인 필요) | Operator | REQUIRED |

### 3.3 Forbidden Transitions (금지)
- inbox → work (claim 누락)
- inbox → pr (Gate/Decision 누락)
- claimed → done (검증/PR 누락)
- done → *(모든 상태) (완료 상태는 종단)

---

## 4) 실행 흐름(고정)

반드시 다음 순서를 따른다:

1) **DRY_RUN**: 변경 적용 없이(Write 금지) 대상/스코프/메트릭 수집  
2) **Diff**: 유니파이드 diff 생성(패치-only)  
3) **Gate**: 정량/정성 게이트 평가(G0~G6)  
4) **Decision**: `AUTO_MERGE` / `PR_ONLY` / `ZERO_STOP`  
5) **APPLY_REQUEST**: Cursor가 패치 적용 + 검증 + 감사로그 append

---

## 5) Gate Pipeline (G0~G6)

| Gate | Name | PASS 조건(요약) | FAIL 시 |
|---|---|---|---|
| G0 | STOP | `.autodev_queue/STOP` **미존재** | 즉시 ZERO_STOP |
| G1 | Daily Go/No-Go | 오늘자 audit 결과 = Go | AUTO_MERGE 금지(PR_ONLY 또는 ZERO_STOP) |
| G2 | Patch Size | 추가+삭제 라인 ≤ **300.00** | AUTO_MERGE 금지(PR_ONLY) |
| G3 | File Safety | dep/lockfile 변경 **0.00**, 삭제 **0.00**, 이진 **0.00** | AUTO_MERGE 금지(PR_ONLY 또는 ZERO_STOP) |
| G4 | Path Allowlist | allowlist_write 내부 변경만 | 즉시 ZERO_STOP |
| G5 | Secrets/NDA | 토큰/키/내부 URL/실경로 원문 **0.00** | 즉시 ZERO_STOP |
| G6 | Audit Append-only | 감사로그 append-only 준수 | 즉시 ZERO_STOP |

---

## 6) Decision Rules (고정)

### 6.1 AUTO_MERGE
다음이 모두 PASS일 때만 허용:
- G0 PASS
- G1 PASS
- G2 PASS
- G3 PASS
- G4 PASS
- G5 PASS
- G6 PASS
- Remote Gate(Protected branch + Required status checks) 상태가 **CONFIRMED** 이고, 체크가 **PASS**(successful/skipped/neutral)인 경우

### 6.2 PR_ONLY
다음 조건에서 선택:
- STOP 없음(G0 PASS)
- allowlist 위반 없음(G4 PASS)
- Secrets 위반 없음(G5 PASS)
- 그러나 G1/G2/G3/G4(Remote CONFIRMED 미충족 포함) 중 1.00개 이상이 PASS가 아닌 경우

### 6.3 ZERO_STOP
다음 중 1.00개라도 충족 시 **STOP 우선**:
- STOP 존재(G0 FAIL)
- allowlist 위반(G4 FAIL)
- Secrets/민감정보 원문 노출(G5 FAIL)
- 감사로그 append-only 위반(G6 FAIL)
- Diff 없이 APPLY 시도(프로세스 위반)

---

## 7) STOP(킬스위치) 규칙

- `.autodev_queue/STOP`가 존재하면, **모든 진행 중 작업은 즉시 중단**한다.
- 현재 작업 폴더는 `blocked/`로 격리한다.
- 감사로그에 아래를 반드시 기록한다:
  - 사유(Operator 입력 또는 UNKNOWN)
  - 위험(데이터 손실/보안/스코프 오염 등)
  - 다음조치(해제 조건/재개 절차)

---

## 8) Daily Go/No-Go 규칙 (AUTO_MERGE 선행조건)

- AUTO_MERGE는 "오늘 audit=Go"를 선행조건으로 요구한다.
- 오늘자 audit 파일은 날짜 형식을 고정한다: `Daily_GoNoGo_YYYY-MM-DD.md`
- audit 결과가 Go가 아니거나 파일이 없으면 AUTO_MERGE는 금지된다.

---

## 9) Remote Gate(브랜치 보호/체크) — CONFIRMED/UNKNOWN 분리

### 9.1 Repo Setting Status

| Item | Status | Value |
|---|---|---|
| Protected branch 사용 여부 | UNKNOWN | UNKNOWN |
| Required status checks 사용 여부 | UNKNOWN | UNKNOWN |
| Required status checks 목록 | UNKNOWN | UNKNOWN |

### 9.2 정책 처리
- 위 상태가 **UNKNOWN**이면, Remote Gate는 PASS로 간주하지 않는다.
- Remote Gate가 UNKNOWN인 동안 Decision은 `PR_ONLY` 또는 `ZERO_STOP`로 제한한다(상위 Gate 결과에 따름).

---

## 10) Output Contract (Agent 응답 포맷)

에이전트 출력은 다음 순서를 고정한다:
1) 요약(5줄 이내)
2) 승인(Go/Revise)
3) patch-only(유니파이드 diff)
4) 검증/로그(PASS/WARN/FAIL + 변경 요약 3줄)
