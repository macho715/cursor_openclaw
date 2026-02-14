# TOOL_POLICY (Policy SSOT) — Allowlist/Denylist

Status: active  
Baton_ID: cursor_setting_policy_lock_v2.0  
Timezone: Asia/Dubai  
Updated: 2026-02-14  
Scope: 정책 문서/설정 텍스트만 (구현/실행/배포 금지)

---

## 0) INPUT REQUIRED (없으면 UNKNOWN)

| Item | Value |
|---|---|
| allowlist_write 경로 | UNKNOWN |
| 기본 브랜치명 | UNKNOWN |
| Required status checks 목록 | UNKNOWN |

---

## 1) 보안 원칙(불변)

1. **Least Privilege**: 필요한 권한만 최소로 허용  
2. **Patch-only**: 변경은 유니파이드 diff 형태로만 제안/승인  
3. **External Exfiltration 기본 차단**: WebChat/외부전송은 우회 경로로 간주  
4. **민감정보 원문 금지**: 토큰/키/내부 URL/실경로는 항상 `<MASKED>`  
5. **Audit Append-only**: 상태 전이/결정/근거는 append-only로 기록

---

## 2) 도구/채널 정책(허용/금지)

### 2.1 파일 시스템(Repo) 접근

| Action | Policy | Notes |
|---|---|---|
| Read | ALLOW | 정책/검증 목적 |
| Write | CONDITIONAL | `allowlist_write=UNKNOWN`이면 **정책 산출물 경로 외 Write 금지** |
| Delete | DENY | 파일 삭제는 기본 금지(0.00) |
| Binary modify | DENY | 이진 변경 0.00 고정 |
| dep/lockfile modify | DENY | dep/lockfile 변경 0.00 고정 |

정책 산출물 경로(본 BATON 범위):
- `docs/policy/**`
- `.cursor/rules/**`

### 2.2 네트워크/외부 호출

| Category | Policy | Notes |
|---|---|---|
| 외부 HTTP 호출 | DENY (기본) | 승인형 예외만 가능 |
| 패키지 다운로드/업데이트 | DENY (기본) | Stage 범위 밖(구현/실행 금지) |
| 공개 문서 조회 | CONDITIONAL | Operator 승인 + 증빙 목적(텍스트-only) |

### 2.3 외부 전송(메일/메신저/업로드)

| Action | Policy | Notes |
|---|---|---|
| 메시지 전송 | DENY (기본) | 우회 경로로 간주 |
| 텍스트-only 알림 | CONDITIONAL | Operator 승인 + `<MASKED>` 적용 |
| 파일 첨부/업로드 | DENY | NDA/PII 리스크 |

### 2.4 Docker Sandbox

| Item | Default | Notes |
|---|---|---|
| 네트워크 | OFF | no-net 기본 |
| 볼륨/마운트 | 최소 | 민감 경로는 `<MASKED>` |
| 실행 | 금지 | Stage 범위(정책 문서)에서는 실행 자체 금지 |

---

## 3) 민감정보 처리(마스킹 규칙)

### 3.1 반드시 마스킹(`<MASKED>`)
- API 토큰/키/세션/쿠키
- 내부 URL(사내/내부 서비스 도메인 포함)
- 절대경로(사용자 홈/드라이브 루트 등)
- 개인 식별 정보(이메일/전화번호/주소 등)

### 3.2 마스킹 포맷
- 토큰/키: `<MASKED>`
- 내부 URL: `<MASKED>`
- 실경로: `<MASKED>`
- 계정/사용자명: `<MASKED>`

---

## 4) 우회 경로 차단 정책(WebChat/외부 채널)

- WebChat/메신저/개인 이메일은 "직접 조작 통로"로 간주한다.
- 기본 정책은 **차단**이며, 예외가 필요하면 다음을 모두 충족해야 한다:
  - Operator 승인(기록)
  - 텍스트-only
  - `<MASKED>` 처리
  - 감사로그 append

---

## 5) 위반 처리

- 1.00건이라도 위반 시: Decision = `ZERO_STOP`
- 작업은 `blocked/`로 격리
- 감사로그에 (위반 항목, 위험, 다음조치) 기록
