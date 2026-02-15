# NEXT PLAN

## 목표
- 현재 구축한 로컬 자동개발 스캐폴딩을 안정 운영 가능한 상태로 고도화.
- 핵심: "제안(Worker)과 적용(Cursor) 권한분리"를 게이트와 감사로그로 강제.

## 우선순위

### P0 (즉시)
1. 외부 보안 마감
- Telegram BotFather에서 기존 토큰 폐기 여부 최종 확인
- 신규 토큰 사용 상태 재검증

2. 워커 기본 모델 정책 고정
- `.env`와 문서에서 기본 모델값 단일화
- `docker-compose.yml` 기본 모델도 동일 값으로 통일 여부 결정

3. Gate 운영 규칙 고정
- Gate FAIL 시 표준 처리:
  - `blocked` 이동
  - 실패 코드별 조치 템플릿 적용

### P1 (단기)
1. Gate 자동 분류 확장
- reason code 세분화:
  - `ALLOWLIST_VIOLATION`
  - `PATCH_NOT_APPLICABLE`
  - `SECRET_PATTERN_DETECTED`
  - `TEST_EVIDENCE_MISSING`
- 코드별 자동 next action 생성

2. 테스트/증적 체계 보강
- task 요구 테스트가 있으면 report에 필수 증적 필드 강제
- `scripts/gate_local.py` 단위 테스트 추가

3. 운영 가시성 강화
- `scripts/summarize_audit.py`에 일별/task별 집계 추가
- PASS/FAIL 비율, 주요 실패코드 Top N 출력

### P2 (중기)
1. Worker 품질 개선
- prompt 템플릿 개선으로 `git apply --check` 통과율 향상
- patch 산출 전 사전 포맷 검증 추가

2. Cursor 적용 파이프라인 표준화
- `candidate.patch` 생성/검증/적용 단계 스크립트화
- 사람 실수(인코딩/경로/리다이렉션) 방지

3. 문서 SSOT 정리
- 런북/워크로그/정책 문서 링크 일원화
- 운영 체크리스트를 단일 문서로 통합

## 실행 순서(권장)
1. P0-1: BotFather 폐기 확인 기록
2. P0-2: 모델 기본값 단일화
3. P0-3: Gate FAIL 처리 규칙 합의/문서화
4. P1-1: 자동 분류 확장 구현
5. P1-2: 게이트 테스트 추가
6. P1-3: 감사로그 요약 개선
7. P2 항목 순차 적용

## 완료 기준 (Definition of Done)
1. 설치/연동
- `ollama launch claude ... -p "MODEL_OK"` 안정 성공

2. 안전성
- diff-only 요청 시 작업트리 delta 0 유지

3. 적용 안전
- Gate PASS 없는 patch는 적용 금지

4. 추적성
- 모든 단계가 `.autodev_queue/audit/events.ndjson`에 기록

## 운영 체크 명령(요약)
```powershell
git status --porcelain
ollama list
claude auth status
python .\scripts\summarize_audit.py
```

