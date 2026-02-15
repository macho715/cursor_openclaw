# BATON_CURRENT (작업 계약 / 단일 세션 기준)

## 세션 ID
- SESSION_ID: 2026-02-15T00:00:00Z
- OWNER: MR.CHA (로컬)

## 역할 분리(변경 금지)
- Claude Code: 작업 티켓(task.json) 생성 및 요구사항 정리
- Cursor(Control-Plane): 리뷰/적용/테스트/커밋/PR/머지 “최종권한”
- OpenClaw(Worker): 패치(diff) 제안만 (repo 적용 금지)
- Ollama: 로컬 LLM 실행

## 목표(Goal)
- task.json 입력을 기반으로, OpenClaw가 **unified diff(.patch)** 와 **리포트(.report.json)** 를 산출한다.

## 산출물(Deliverables)
- `.autodev_queue/work/<task_id>.patch`
- `.autodev_queue/work/<task_id>.report.json`
- `.autodev_queue/audit/events.ndjson` 에 append-only 이벤트 추가

## 금지(Non-goals)
- OpenClaw가 repo 파일을 수정/커밋/푸시/머지하는 행위 금지
- 비밀정보(토큰/키/계정) 프롬프트/로그 반출 금지
- allowlist 밖 파일 변경 제안 금지(필요 시 NEED_INPUT로 반려)

## 안전장치(Safety)
- 기본 DRY_RUN=1
- Kill-switch: `.autodev_queue/STOP` 존재 시 즉시 중단
- Repo는 컨테이너에서 read-only 마운트
