# Claude Code + Cursor + OpenClaw + Ollama (Queue-based) 스캐폴딩

## 목표
- OpenClaw Worker는 **패치(diff)만 생성**
- Cursor(Control-Plane)만 **apply/test/commit**
- Claude Code는 **작업 티켓(task.json) 생성**까지

## 빠른 시작
1) 큐 초기화
   - ./scripts/init_queue.sh

2) Ollama 기동
   - docker compose up -d

3) (선택) 워커 기동(빌드 포함)
   - docker compose --profile worker up -d --build

4) task 투입
   - ./scripts/submit_task.sh "./tasks/task_template.json"

5) 산출물 확인
   - .autodev_queue/work/*.patch
   - .autodev_queue/work/*.report.json

## Cursor에서 적용 절차(권장)
- patch 검토
- Gate 스크립트 실행(강화형):
  - `./scripts/gate_local.sh <patch> <task_json> <report_json>`
  - 자동 체크: unified diff, allowlist/denylist 경로, touched files, patch apply 가능성, 테스트 증적
- git apply <patch>
- 테스트/린트
- commit/PR

## Kill-switch
- .autodev_queue/STOP 파일이 존재하면 워커는 즉시 중단하고, 들어온 task는 blocked로 이동.
