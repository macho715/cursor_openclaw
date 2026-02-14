
# A11Y_DoD.md
(WCAG 2.2 AA 목표, 컴포넌트 단위 DoD)

## 목표
- WCAG 2.2 AA 기준을 “컴포넌트 DoD + 테스트 체크리스트”로 강제한다.
- 특히 신규 SC: Focus Not Obscured(2.4.11), Dragging Movements(2.5.7), Target Size(2.5.8), Consistent Help(3.2.6), Redundant Entry(3.3.7), Accessible Authentication(3.3.8)를 필수로 포함.

## 컴포넌트 공통 DoD
1) Keyboard
- 탭 순서 논리적, 모든 주요 CTA 키보드로 접근 가능
- 모달/드로어는 포커스 트랩 + ESC 종료 + 포커스 복귀

2) Focus Not Obscured (Minimum)
- 포커스가 배너/토스트/모달 뒤에 “완전히 가려지지” 않게 레이아웃/스크롤 보정

3) Dragging Movements
- 드래그 기반 조작(예: 큐 재정렬)은 버튼/키보드 대체 제공

4) Target Size (Minimum)
- 주요 타깃(버튼/아이콘)은 최소 24x24 CSS px 충족(예외는 명시)

5) Error & Help
- 에러 메시지: 원인+해결책 1줄 포함, 필드와 프로그램적 연결(aria-describedby 등)
- Help(링크/문의/가이드) 위치는 화면 간 일관

6) Redundant Entry
- S2에서 읽은 정보(allowlist/commands/risk)는 S3~S6에서 재입력 요구 금지(자동 채움)

7) Accessible Authentication(해당 시)
- 인증 단계에서 기억/퍼즐 같은 인지 테스트 강제 금지, 대체 수단 제공

## 테스트 체크(필수)
- 키보드-only: S1→S7 완주 가능
- 200% 줌: 레이아웃 붕괴/포커스 가림 없음
- 모바일 터치: 타깃 크기/간격 충족
- 스크린리더(기본): 버튼/표/뱃지 라벨 읽힘
- 오류 시나리오: INPUT_MISSING, LOCK_CONFLICT, ZERO_STOP 안내가 “단일 문장”으로 이해 가능
