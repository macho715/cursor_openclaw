# RECOVERY_PLAYBOOK — R1~R8 Skill-level Mapping (Reference-only)

## 원칙
- R1~R8 "정의/절차"는 Stage 5 SSOT(`../../AGENTS.md`)에 있음.
- 본 문서는 "어떤 상황에서 어떤 R#을 호출(참조)하는지"만 매핑한다.
- (가정) 아래 매핑은 보수적 추천안이며, SSOT와 다르면 SSOT가 우선.

| Scenario | Trigger | Recommended Recovery Ref | Called by Skill | Notes |
|---|---|---|---|---|
| Lock 충돌 | LOCK_CONFLICT | R1 | claim-lock | 재시도 금지, blocked 수렴 권장 |
| Intake 실패 | missing/invalid/protected | R2 | intake-validate | allowlist/Protected 위반 시 ZERO_STOP |
| Diff 위험 높음 | delete/lockfile/high risk | R3 | diff-risk-scan | PR_ONLY 또는 ZERO_STOP로 다운그레이드 |
| Gate 실패 | G1~G6 FAIL | R4 | gate-runner | evidence 필수 |
| PR checks 실패 | CI/checks fail | R5 | pr-merge-orchestrator | AUTO_MERGE 금지 |
| Apply 롤백 | apply 후 문제 | R6 | pr-merge-orchestrator | Cursor 소유 |
| Audit append 실패 | append-only 실패 | R7 | audit-append | 기록 불가 자체가 incident |
| Incident 에스컬레이션 | SEV1/정책 위반 | R8 | incident-brief | 알림 템플릿 필수 |
