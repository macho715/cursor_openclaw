# AutoDev Telegram Orchestrator (Mode B) — Full Pack

## 이 팩이 하는 일
- Telegram에서 `/work 텍스트` 입력
- Claude Code(Ollama)로 diff 제안 생성(자동)
- 로컬 Gate:
  - `git status --porcelain=v2` clean 확인
  - `git apply --check` 통과 확인
- PASS/FAIL 요약을 Telegram으로 1회 전송
- 적용/커밋/푸시는 사람이(Cursor) 수행

## 빠른 설치(Windows)
1) 이 폴더 내용을 repo 루트에 복사/덮어쓰기(권장: 백업)
2) `.env.example` → `.env` 복사 후 `TG_BOT_TOKEN` 입력
3) 설치/디렉토리 생성:
   - `powershell -ExecutionPolicy Bypass -File .\scripts\install_windows.ps1`
4) 실행:
   - `powershell -ExecutionPolicy Bypass -File .\scripts\run_orchestrator.ps1`

## Telegram 커맨드
- `/help`
- `/status`
- `/work <텍스트>`
- `/stop` / `/resume`

## 파일 구조
- `orchestrator/tg_orchestrator.py` : TG 폴링 + Gate + 리포트
- `config/WORK_AUTODEV_CONFIG.json` : 모든 세팅 값(풀 옵션)
- `docs/MODE_B_TELEGRAM_AUTOMATION.md` : 운영 문서
- `scripts/*.ps1` : 설치/실행/스케줄 작업/STOP

## 보안
- `.env`는 절대 커밋 금지
- 토큰 노출 시 BotFather에서 즉시 Revoke/재발급


## 1-커맨드 실행(원샷)
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\quick_start.ps1
```

## 2단 승인(무인→사람)
- Telegram에서 `/work ...` → PASS 받기
- Telegram에서 `/approve <task_id>` → 승인 플래그 생성
- Cursor에서 `scripts\cursor_apply_approved.ps1` 실행해 patch 적용(수동 커밋)
