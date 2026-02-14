
# TOOL_POLICY.md (SSOT)

## Cursor(Control-Plane)
- 허용: allowlist 경로 파일 작업, Gate 실행(lint/test/build), Git PR/Merge(승인/게이트 충족 전제), 감사로그 append
- 금지: 외부 업로드/전송, 비밀값 저장/출력

## OpenClaw(Worker)
- 허용: 인테이크 파일 읽기, patch_draft.diff + rationale.md 작성(제안)
- 금지: APPLY/TEST/COMMIT/PR/MERGE, Git 조작, 네트워크, 외부 채널 전송
