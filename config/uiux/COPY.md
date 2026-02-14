
# COPY.md
(경고/배너/모달 문구 — 마스킹/보안 기본)

## 1) STOP 배너(상단 고정)
- 제목: "긴급 중단(STOP) 활성화"
- 본문: "모든 실행(Generate/Gate/APPLY/PR/Merge)이 차단되었습니다. Incident 화면에서 원인/복구 절차를 확인하세요."
- CTA: "Incident 열기"

## 2) Protected Zones 경고(모달)
- 제목: "보호구역 접근 감지"
- 본문: "이 작업은 Protected Zones를 포함합니다. 정책상 자동 중단(ZERO_STOP) 대상입니다."
- CTA: "Blocked로 이동" / "닫기(읽기전용)"

## 3) AUTO_MERGE 조건 안내(인포 패널)
- "AUTO_MERGE는 아래 조건을 모두 만족할 때만 가능합니다:"
  - "라인(add+del) ≤ 300.00"
  - "파일 삭제 0.00"
  - "dep/lockfile 변경 0.00"
  - "allowlist 경로만 변경"
  - "lint/test/build PASS"
  - "DRY_RUN↔APPLY 일치"

## 4) PR_ONLY 안내(토스트)
- "자동 머지 조건 미충족: PR_ONLY로 전환되었습니다. 리뷰 후 Merge 하세요."

## 5) ZERO_STOP 안내(모달)
- 제목: "정책 위반으로 중단(ZERO_STOP)"
- 본문(템플릿):
  - "사유: {REASON}"
  - "위험: 데이터 손실/유출/권한 오남용 가능성"
  - "다음: Incident에서 복구(재시도/롤백/알림)를 진행하세요."
- CTA: "Incident 열기"

## 6) WebChat 제한 안내(라벨)
- "WebChat은 우회 경로로 간주되어 읽기전용입니다(기본 비활성)."

## 7) 외부 전송 차단 안내(에러)
- "외부 전송/업로드는 차단되어 있습니다. 운영자 알림은 ‘텍스트’만 허용됩니다(민감정보 자동 마스킹)."
