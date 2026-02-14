# AGENTS.md (SSOT)

이 문서는 에이전트 실행/운영 정책의 단일 진실원(SSOT) 참조점이다.
세부 정책 본문은 아래 문서를 우선순위대로 따른다.

## 1. SSOT 우선순위
1. `config/policy/CURSOR_RULES.md`
2. `config/policy/TOOL_POLICY.md`
3. `config/policy/APPROVAL_MATRIX.md`
4. `config/policy/AUDIT_LOG_SCHEMA.md`
5. `config/uiux/UX_FLOW.md`
6. `config/uiux/SCREENS.md`
7. `config/uiux/INPUT_GUARD.md`
8. `config/uiux/A11Y_DoD.md`
9. `config/uiux/COPY.md`
10. `config/uiux/COMPONENTS.md`

## 10. Options A/B/C
- **Option A (기본)**: 저위험 조건 충족 시 AUTO_MERGE 허용.
- **Option B**: PR_ONLY 중심, 사람 리뷰 강제.
- **Option C**: ZERO_STOP 중심, 운영자 개입 전제.

## 11. Roadmap
- Prepare → Pilot → Build → Operate → Scale
- KPI/기간은 `docs/ROADMAP.md`를 운영 가이드로 따르되, 정책 충돌 시 본 SSOT 체계를 우선한다.
