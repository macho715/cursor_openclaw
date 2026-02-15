# POLICY (SSOT)

## 1) 권한 행렬
| Actor | Allowed | Forbidden |
|---|---|---|
| Claude Code | task.json 생성, 요구사항/성공조건 작성 | repo 적용/커밋/머지 |
| Cursor | apply/test/commit/PR/merge, gate decision | worker 역할(LLM patch 자동적용) |
| OpenClaw | repo read, diff 제안, 산출물 저장, audit 기록 | apply/commit/merge, 토큰 사용 |
| Ollama | 로컬 생성 응답 | 외부 전송/원격 업로드 |

## 2) Gate 규칙(필수)
- (G1) STOP 존재 → 즉시 FAIL
- (G2) allowlist 외 파일 touched → FAIL
- (G3) unified diff 형식 아님 → FAIL
- (G4) 리스크 플래그(키/토큰/자격증명 패턴 탐지) → FAIL
- (G5) 테스트 요구가 있는 task인데 테스트 증적 없으면 → FAIL 또는 NEED_INPUT

## 3) 산출물 규격
- patch: git apply 가능한 unified diff
- report: JSON (status, summary, files_touched, risks, next_actions)

## 4) 로그(append-only)
- 모든 주요 상태 전이(Submitted/Claimed/Proposed/Blocked/Done)는 NDJSON 이벤트로 기록
