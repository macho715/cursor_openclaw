from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from .state_machine import QueuePaths, QueueState, has_stop, move_task


class GateError(RuntimeError):
    pass


@dataclass(frozen=True)
class GateResult:
    gate_id: str
    passed: bool
    reason: str = ""


def task_artifacts_dir(task_dir: Path) -> Path:
    return task_dir / "artifacts"


def require_task_in_state(task_id: str, state: QueueState, qp: QueuePaths | None = None) -> Path:
    qp = qp or QueuePaths()
    st, p = qp.find_task(task_id)
    if st != state:
        raise GateError(f"INVALID_TASK_STATE: expected={state.value} actual={st.value}")
    return p


def require_no_stop(task_dir: Path, task_id: str, qp: QueuePaths | None = None) -> None:
    if has_stop(task_dir):
        qp = qp or QueuePaths()
        # best effort: move to blocked if allowed from current state
        try:
            move_task(task_id, QueueState.BLOCKED, qp=qp)
        except Exception:
            pass
        raise GateError("STOP_DETECTED")


def require_dry_run(task_dir: Path) -> Path:
    p = task_artifacts_dir(task_dir) / "dry_run.json"
    if not p.exists():
        raise GateError("DRY_RUN_REQUIRED")
    return p


def require_diff(task_dir: Path) -> Path:
    p = task_artifacts_dir(task_dir) / "diff.patch"
    if not p.exists():
        raise GateError("DIFF_REQUIRED")
    return p


def run_gate_pipeline(task_id: str, qp: QueuePaths | None = None) -> List[GateResult]:
    qp = qp or QueuePaths()
    qp.ensure_dirs()
    # allow gating only from work or pr (strict)
    st, task_dir = qp.find_task(task_id)
    if st not in (QueueState.WORK, QueueState.PR):
        raise GateError(f"GATE_NOT_ALLOWED_FROM_STATE: {st.value}")

    require_no_stop(task_dir, task_id, qp=qp)
    require_dry_run(task_dir)
    require_diff(task_dir)

    # Policy-defined G0~G6 (placeholder skeleton): pass/fail list
    results: List[GateResult] = []
    for gid in ["G0", "G1", "G2", "G3", "G4", "G5", "G6"]:
        results.append(GateResult(gate_id=gid, passed=True, reason="OK"))

    return results


def gate_passed(results: List[GateResult]) -> bool:
    return all(r.passed for r in results)
