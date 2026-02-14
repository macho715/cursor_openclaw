from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .audit_logger import AuditLogger
from .gates import GateError, gate_passed, run_gate_pipeline
from .state_machine import QueuePaths, QueueState, has_stop, move_task


DecisionType = Literal["AUTO_MERGE", "PR_ONLY", "ZERO_STOP"]


@dataclass(frozen=True)
class Decision:
    decision: DecisionType
    reason: str


def decide(task_id: str, audit: AuditLogger, qp: QueuePaths | None = None) -> Decision:
    qp = qp or QueuePaths()
    st, task_dir = qp.find_task(task_id)

    if has_stop(task_dir):
        try:
            move_task(task_id, QueueState.BLOCKED, qp=qp)
        except Exception:
            pass
        audit.append_event({"task_id": task_id, "event": "DECIDE", "decision": "ZERO_STOP", "reason": "STOP_DETECTED"})
        return Decision(decision="ZERO_STOP", reason="STOP_DETECTED")

    try:
        results = run_gate_pipeline(task_id, qp=qp)
    except GateError as e:
        # Gate entry failure is ZERO_STOP
        try:
            move_task(task_id, QueueState.BLOCKED, qp=qp)
        except Exception:
            pass
        audit.append_event({"task_id": task_id, "event": "DECIDE", "decision": "ZERO_STOP", "reason": str(e)})
        return Decision(decision="ZERO_STOP", reason=str(e))

    if not gate_passed(results):
        try:
            move_task(task_id, QueueState.BLOCKED, qp=qp)
        except Exception:
            pass
        audit.append_event({"task_id": task_id, "event": "DECIDE", "decision": "ZERO_STOP", "reason": "GATE_FAILED"})
        return Decision(decision="ZERO_STOP", reason="GATE_FAILED")

    # Stage4: never actually merge; default PR_ONLY
    audit.append_event({"task_id": task_id, "event": "DECIDE", "decision": "PR_ONLY", "reason": "GATES_OK"})
    return Decision(decision="PR_ONLY", reason="GATES_OK")
