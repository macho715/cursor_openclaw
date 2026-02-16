# MODE B Telegram 자동화(Full Pack)

## 목표
- PC 켜두고 출근
- Telegram에서 `/work 텍스트`로 지시
- 자동으로 **diff 제안 + 로컬 Gate(검증) + report 생성 + Telegram 요약 전송**
- 적용/커밋/푸시는 **사람(Cursor)** 만 수행

## 핵심 원칙(절대)
1) 자동은 **제안/검증/리포트**까지만 (apply/commit/push 금지)
2) SSOT는 로컬 Git:
   - `git status --porcelain=v2` clean 아니면 STOP
   - `git apply --check` PASS(0) 아니면 FAIL
3) Kill-switch:
   - `.autodev_queue/STOP` 존재 시 즉시 중단

## 설치(Windows, repo 루트에서)
1) 이 팩을 **repo 루트**에 풀기
2) `.env.example` → `.env` 복사 후 `TG_BOT_TOKEN` 입력
3) (권장) `.gitignore`에 아래 추가 후 커밋:
   - `.autodev_runtime/`
   - `logs/`
   - `.env`
   - `patches/` (이미 ignore 처리된 상태면 스킵)

## 실행
### 수동 실행(권장: 먼저 이걸로 검증)
```powershell
cd <repo_root>
python .\orchestrator\tg_orchestrator.py
```

### Telegram에서 테스트
- `/help`
- `/status`
- `/work README 첫 줄 끝에 (PROPOSED) 추가`

## 결과 해석
- `[STOP] Repo dirty` : 커밋/스태시 등으로 clean 만들고 재시도
- `[FAIL] Patch invalid` : 프롬프트/요구사항을 더 구체화
- `[PASS] Patch proposed` : Cursor에서 patch 리뷰 후 적용

## 주의(보안)
- TG 토큰은 외부 노출 즉시 **Revoke/재발급**
- `.env`는 절대 커밋 금지


## 2단 승인 흐름(무인→사람)

1) Telegram: `/work <텍스트>`
   - 결과가 `[PASS] Patch proposed`로 오면 task_id를 확인
2) Telegram: `/approve <task_id>` (또는 `/approve` = 마지막 PASS 작업)
   - 오케스트레이터는 **승인 플래그만 생성**: `.autodev_queue/approved/<task_id>.approved.json`
3) Cursor에서만 적용:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\cursor_apply_approved.ps1
# 또는 특정 작업
# powershell -ExecutionPolicy Bypass -File .\scripts\cursor_apply_approved.ps1 -TaskId T20260215-091500
```

