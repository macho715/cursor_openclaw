from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .audit_logger import AuditLogger
from .audit_paths import audit_path
from .gates import GateError, gate_passed, run_gate_pipeline
from .state_machine import (
    QueuePaths,
    QueueState,
    TransitionError,
    has_global_stop,
    has_stop,
    move_task,
)

DecisionType = Literal["AUTO_MERGE", "PR_ONLY", "ZERO_STOP"]


@dataclass(frozen=True)
class Decision:
    decision: DecisionType
    reason: str


def _audit(qp: QueuePaths, task_id: str) -> AuditLogger:
    return AuditLogger(audit_path(task_id, qp))


def _append_decision_log(
    qp: QueuePaths, task_id: str, decision: DecisionType, reason: str
) -> None:
    # Re-check current task location so logging stays consistent after move_task calls.
    qp.find_task(task_id)
    _audit(qp, task_id).append_event(
        {"task_id": task_id, "event": "DECIDE", "decision": decision, "reason": reason}
    )


def decide(task_id: str, qp: QueuePaths | None = None) -> Decision:
    qp = qp or QueuePaths()
    _, task_dir = qp.find_task(task_id)
    audit = _audit(qp, task_id)

    if has_global_stop(qp):
        try:
            move_task(task_id, QueueState.BLOCKED, qp=qp)
        except TransitionError as e:
            audit.append_event(
                {
                    "task_id": task_id,
                    "event": "DECIDE_BLOCK_MOVE_SKIPPED",
                    "reason": str(e),
                }
            )
        audit.append_event(
            {
                "task_id": task_id,
                "event": "GLOBAL_STOP_DETECTED",
                "reason": "STOP_DETECTED",
            }
        )
        audit.append_event(
            {
                "task_id": task_id,
                "event": "DECIDE",
                "decision": "ZERO_STOP",
                "reason": "STOP_DETECTED",
            }
        )
        return Decision(decision="ZERO_STOP", reason="STOP_DETECTED")

    if has_stop(task_dir):
        try:
            move_task(task_id, QueueState.BLOCKED, qp=qp)
        except TransitionError as e:
            audit.append_event(
                {
                    "task_id": task_id,
                    "event": "DECIDE_BLOCK_MOVE_SKIPPED",
                    "reason": str(e),
                }
            )
        audit.append_event(
            {
                "task_id": task_id,
                "event": "DECIDE",
                "decision": "ZERO_STOP",
                "reason": "STOP_DETECTED",
            }
        )
        return Decision(decision="ZERO_STOP", reason="STOP_DETECTED")

    try:
        results = run_gate_pipeline(task_id, qp=qp, audit=audit)
    except GateError as e:
        # Gate entry failure is ZERO_STOP
        try:
            move_task(task_id, QueueState.BLOCKED, qp=qp)
        except TransitionError as move_err:
            audit.append_event(
                {
                    "task_id": task_id,
                    "event": "DECIDE_BLOCK_MOVE_SKIPPED",
                    "reason": str(move_err),
                }
            )
        audit.append_event(
            {
                "task_id": task_id,
                "event": "DECIDE",
                "decision": "ZERO_STOP",
                "reason": str(e),
            }
        )
        return Decision(decision="ZERO_STOP", reason=str(e))

    if not gate_passed(results):
        failed = [f"{r.gate_id}:{r.reason}" for r in results if not r.passed]
        failure_reason = f"GATE_FAILED:{'|'.join(failed)}"
        try:
            move_task(task_id, QueueState.BLOCKED, qp=qp)
        except TransitionError as e:
            audit.append_event(
                {
                    "task_id": task_id,
                    "event": "DECIDE_BLOCK_MOVE_SKIPPED",
                    "reason": str(e),
                }
            )
        audit.append_event(
            {
                "task_id": task_id,
                "event": "DECIDE",
                "decision": "ZERO_STOP",
                "reason": failure_reason,
            }
        )
        return Decision(decision="ZERO_STOP", reason=failure_reason)

    # Stage4: never actually merge; default PR_ONLY
    audit.append_event(
        {
            "task_id": task_id,
            "event": "DECIDE",
            "decision": "PR_ONLY",
            "reason": "GATES_OK",
        }
    )
    return Decision(decision="PR_ONLY", reason="GATES_OK")
