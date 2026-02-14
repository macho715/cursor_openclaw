# 시스템 전체 로드맵 플랜

Control-Plane Cursor / Worker OpenClaw — Folder Queue Option A

---

## 1. 목적·범위

- 본 문서는 **시스템 전체** 관점의 단계별 계획(Prepare → Pilot → Build → Operate → Scale)을 정리한다.
- **Option A** 기준: 저위험 AUTO_MERGE 허용(조건 충족 시). KPI·기간은 가이드이며, 정책 SSOT(`AGENTS.md`, `config/policy`)에 우선하지 않는다.
- 로드맵은 “계획 문서”이며, 실행 시 항상 STOP·allowlist·민감정보 정책을 준수한다.

---

## 2. 단계별 로드맵

(출처: `AGENTS.md` §11 Roadmap)

| 단계 | 산출물 | KPI(필수) | 기간(가이드) |
|------|--------|-----------|--------------|
| **Prepare** | UX_FLOW / SCREENS / INPUT_GUARD / A11Y / COPY / COMPONENTS 확정 | 삭제 0.00, 승인 없는 실행 0.00 | 1.00주 |
| **Pilot** | Option A로 제한 범위(allowlist 좁게) 시범 | DRY_RUN↔APPLY 일치 ≥ 99.00% | 2.00주 |
| **Build** | Gate 결과/감사로그 표준화, Incident 복구 경로 닫기 | ZERO_STOP 원인 상위 3.00개 제거 | 2.00주 |
| **Operate** | 운영 대시(Queue health, stuck, gate fail rate) | 승인 누락 0.00, 우회(WebChat) 0.00 | 상시 |
| **Scale** | allowlist 확장(단계적), AUTO_MERGE 범위 확대 | AUTO_MERGE 성공률 ≥ 70.00% (가정) | 상시 |

---

## 3. 단계별 상세

### 3.1 Prepare

- **목표**: UI/UX·입력 가드·접근성·카피·컴포넌트 스펙을 “고정”하여, 이후 단계에서 동일 기준으로 검증 가능하게 한다.
- **산출물**: `config/uiux/` — UX_FLOW, SCREENS, INPUT_GUARD, A11Y_DoD, COPY, COMPONENTS.
- **KPI**: 파일 삭제 0건, 승인 없이 실행 0건(Approve-to-Run 강제).
- **완료 조건**: S2 Input Guard로 “뭘 넣어야 하죠?”가 불필요한 수준으로 정리됨.

### 3.2 Pilot

- **목표**: Option A 정책으로 **제한된 allowlist** 안에서만 시범 운영하여, DRY_RUN과 APPLY 결과가 일치하는지 검증한다.
- **산출물**: allowlist 좁게 유지, Queue·Gate·Decision 실제 1회 이상 주기 완료.
- **KPI**: DRY_RUN↔APPLY 일치율 ≥ 99.00%.
- **완료 조건**: 시범 구간에서 ZERO_STOP/우회 없이 정상 경로로 done/ 도달 사례 확보.

### 3.3 Build

- **목표**: Gate 결과·감사로그 형식을 표준화하고, Incident 발생 시 복구 경로(Containment → Recovery → Resume)를 문서·절차로 “닫는다”.
- **산출물**: GATES.md/gate_results.json 형식 고정, `.cursor/commands/queue-run-gates`, `incident-recover` 등 절차 정리, audit 스키마 준수.
- **KPI**: ZERO_STOP 원인 상위 3개를 식별·대응하여 재발 감소.
- **완료 조건**: S7 Incident에서 복구 체크리스트·리포트 템플릿으로 일관되게 대응 가능.

### 3.4 Operate

- **목표**: 상시 운영 시 Queue 상태·stuck 작업·Gate 실패율을 모니터링하고, 승인 누락·우회(WebChat/외부 전송)가 없도록 유지한다.
- **산출물**: 운영 대시(또는 주기 점검) — Queue health, stuck, gate fail rate.
- **KPI**: 승인 누락 0.00, 우회(WebChat) 0.00.
- **완료 조건**: 정책상 “상시”이므로, 주기적 점검으로 KPI 유지.

### 3.5 Scale

- **목표**: allowlist를 단계적으로 확장하고, 조건 충족 시 AUTO_MERGE 허용 범위를 넓혀 무인 처리율을 높인다.
- **산출물**: allowlist 확대(경로 추가), AUTO_MERGE 조건·리뷰 정책 재검토.
- **KPI**: AUTO_MERGE 성공률 ≥ 70.00%(가정).
- **완료 조건**: 정책상 “상시”이므로, 단계별 확대 후 KPI 모니터링.

---

## 4. Stage와의 관계

| MANIFEST | 의미 | 로드맵 단계와의 대응(가이드) |
|----------|------|-----------------------------|
| `stage_current=3` | Cursor Project Setting(문서/정책/레일) | Prepare·Pilot·Build 초반 |
| `stage_next=4` | 코드 구현 단계 전달 | Build 후반·Operate·Scale |

- **BATON_CURRENT.md**: “Stage 3 → 4: Cursor 규칙/스킬/레일을 변경 없이 코드 구현 단계로 전달.”
- Stage 전환 시점은 운영 정책에 따르며, 로드맵 단계와 1:1로 고정되지 않는다.

---

## 5. 단계 간 의존성

- **Prepare** 완료 후 **Pilot** 진행(UX/입력 가드 미확정 시 시범 결과 해석 어려움).
- **Pilot** 결과(DRY_RUN↔APPLY 일치율) 확보 후 **Build**에서 Gate/감사·Incident 표준화.
- **Build**에서 복구 경로가 닫힌 뒤 **Operate** 상시 운영으로 전환.
- **Operate** 안정화 후 **Scale**(allowlist·AUTO_MERGE 확대).

---

## 6. 리스크·제약

- **STOP**: 로드맵 어느 단계에서도 `.autodev_queue/STOP` 존재 시 즉시 중단·격리. 재개는 Operator 승인 후에만.
- **allowlist**: 확장은 단계적. 보호구역·정책 경로 위반 시 ZERO_STOP.
- **민감정보**: 토큰/키/내부 URL/실경로 원문 금지, `<MASKED>` 처리. UNKNOWN은 가정하지 않고 유지.
- **우회 경로**: WebChat/외부 전송은 기본 비활성·읽기전용. 운영자 알림은 텍스트-only·마스킹 필수.

---

## 7. 참조

- **에이전트·정책 SSOT**: [AGENTS.md](../AGENTS.md) §11 Roadmap, §10 Options A/B/C
- **현재 Stage**: [MANIFEST.json](../MANIFEST.json), [BATON_CURRENT.md](../BATON_CURRENT.md)
- **아키텍처**: [docs/ARCHITECTURE.md](ARCHITECTURE.md)
- **README**: [README.md](../README.md)
