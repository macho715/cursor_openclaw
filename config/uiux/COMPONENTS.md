
# COMPONENTS.md
(컴포넌트 목록 + 상태)

## Core Components
- StopBanner
  - states: hidden | active
  - a11y: role="status", focusable link to Incident

- QueueTable
  - props: folder(inbox/claimed/work/pr/done/blocked), rows, filters
  - states: loading | empty | error | normal
  - a11y: table semantics, keyboard row navigation

- TaskCard
  - props: task_id, risk, last_updated, status_badges
  - states: normal | locked | blocked

- RiskBadge
  - values: LOW | MED | HIGH
  - color-only 금지(텍스트 병기)

- TaskDetailPanel
  - tabs: task.md | acceptance.md | risk.json | allowlist | commands | notes
  - states: valid | missing_required | policy_denied

- PlanEditor (읽기+제안 중심)
  - sections: Scope | Tests | Rollback | Risks
  - states: draft | ready

- DiffViewer (읽기전용)
  - features: file tree, inline diff, summary counters(add/del/delete/lockfile)
  - states: ok | parse_fail | policy_flagged

- GateTable
  - rows: G0~G6, PASS/FAIL, evidence_ref
  - states: not_run | running | done

- EvidencePanel
  - shows: logs hash, timestamps, actor, artifacts
  - states: partial | complete

- ApprovalModal
  - summary: “무엇을/어디에/되돌리기/위험”
  - actions: Approve | Cancel

- PRStatusCard
  - shows: PR link placeholder, checks status, auto-merge eligibility reasons

- AuditDrawer (append-only)
  - filters: task_id, actor, date
  - states: loading | empty | normal

- IncidentConsole
  - shows: reason, impact, recovery checklist, notify template(text-only)

## Global UI State (요약)
- stop_mode: boolean
- selected_task_id: string|null
- approval_state: not_requested | pending | approved | cancelled
- gate_state: not_run | running | pass | fail_soft | fail_hard
- decision: AUTO_MERGE | PR_ONLY | ZERO_STOP
