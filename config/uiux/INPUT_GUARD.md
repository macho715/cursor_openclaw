
# INPUT_GUARD.md
(필수 입력 + 보호구역 DENY + 외부전송 차단)

## 1) 필수 입력(없으면 진행 불가)
- risk: LOW | MED | HIGH
- allowlist.txt: 변경 허용 경로(상대경로, 폴더 단위 권장)
- commands.md: lint / test / build (문자열로만)
- max-lines: 300.00 (Option A 기본값, 변경 불가 또는 운영자만 변경)

## 2) risk.json 최소 스키마(예시)
- risk: "LOW|MED|HIGH"
- rationale: "왜 이 등급인가(1~3줄)"
- external_io: false (고정)
- data_sensitivity: "P0|P1|P2" (P2 포함 시 자동 PR_ONLY 또는 ZERO_STOP)
- max_lines: 300.00
- allow_delete: false (고정)
- allow_lockfile: false (고정)

## 3) Protected Zones (기본 DENY, 설계 명시)
- 사용자 문서/바탕화면/다운로드/사진/동영상/음악
- 브라우저 프로필/세션/쿠키 저장소
- 키스토어/비밀키/SSH 키/자격증명 저장소
- 클라우드 동기화 폴더(예: OneDrive/Drive 계열)
- 시스템/프로그램 파일 영역
- .env, *.pem, *.key, credentials* 등 민감 패턴

UI 동작(고정):
- allowlist가 Protected Zones를 포함하면 즉시 BLOCK + ZERO_STOP 후보로 표시

## 4) 외부 전송/업로드 차단(고정)
- 웹업로드/파일전송/외부 채널(텔레그램 등) 기능은 “설계상 미제공”
- 허용: 운영자 알림용 “텍스트 메시지” (내용은 PII/토큰/경로 마스킹)

## 5) WebChat 우회 경로 정책(UX 가정)
- WebChat 입력: 기본 비활성
- WebChat 출력: 읽기전용(로그/상태 조회만)

## 6) 자동머지(Option A) 입력 고정값
- (add+del) ≤ 300.00
- dep/lockfile 변경 0.00
- 파일 삭제 0.00
- allowlist 경로만 변경
- lint/test/build PASS
- DRY_RUN↔APPLY 일치
