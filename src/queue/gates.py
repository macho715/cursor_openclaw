from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List

from .audit_logger import AuditLogger
from .state_machine import (
    QueuePaths,
    QueueState,
    TransitionError,
    has_global_stop,
    has_stop,
    move_task,
)

MAX_LINES = 300.00
LOCK_OR_DEP_PATTERNS = (
    "poetry.lock",
    "pdm.lock",
    "uv.lock",
    "Pipfile.lock",
    "requirements.txt",
    "requirements-dev.txt",
    "pyproject.toml",
    "Cargo.lock",
    "Cargo.toml",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
)


class GateError(RuntimeError):
    pass


@dataclass(frozen=True)
class GateResult:
    gate_id: str
    passed: bool
    reason: str = ""


@dataclass(frozen=True)
class DiffMetrics:
    added_lines: int
    deleted_lines: int
    touched_files: tuple[str, ...]


def task_artifacts_dir(task_dir: Path) -> Path:
    return task_dir / "artifacts"


def require_task_in_state(
    task_id: str, state: QueueState, qp: QueuePaths | None = None
) -> Path:
    qp = qp or QueuePaths()
    st, p = qp.find_task(task_id)
    if st != state:
        raise GateError(f"INVALID_TASK_STATE: expected={state.value} actual={st.value}")
    return p


def require_no_stop(
    task_dir: Path,
    task_id: str,
    qp: QueuePaths | None = None,
    audit: AuditLogger | None = None,
) -> None:
    if has_stop(task_dir):
        qp = qp or QueuePaths()
        # best effort: move to blocked if allowed from current state
        try:
            move_task(task_id, QueueState.BLOCKED, qp=qp)
        except TransitionError as e:
            if audit:
                audit.append_event(
                    {
                        "task_id": task_id,
                        "event": "STOP_BLOCK_MOVE_SKIPPED",
                        "reason": str(e),
                    }
                )
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


def _load_dry_run(dry_run_path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(dry_run_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GateError(f"DRY_RUN_INVALID_JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise GateError("DRY_RUN_INVALID_SHAPE")
    return payload


def _read_diff_metrics(diff_path: Path) -> DiffMetrics:
    added_lines = 0
    deleted_lines = 0
    touched_files: list[str] = []
    for raw_line in diff_path.read_text(encoding="utf-8").splitlines():
        if raw_line.startswith("+++ b/"):
            touched_files.append(raw_line.removeprefix("+++ b/"))
            continue
        if raw_line.startswith("--- a/"):
            continue
        if raw_line.startswith("+"):
            added_lines += 1
            continue
        if raw_line.startswith("-"):
            deleted_lines += 1
    return DiffMetrics(
        added_lines=added_lines,
        deleted_lines=deleted_lines,
        touched_files=tuple(touched_files),
    )


def _dry_run_bool(dry_run: dict[str, Any], key: str) -> tuple[bool, str]:
    value = dry_run.get(key)
    if not isinstance(value, bool):
        return False, f"DRY_RUN_FIELD_INVALID:{key}"
    if not value:
        return False, f"{key.upper()}_FAILED"
    return True, "OK"


def check_g0_stop(task_dir: Path) -> GateResult:
    if has_stop(task_dir):
        return GateResult(gate_id="G0", passed=False, reason="STOP_DETECTED")
    return GateResult(gate_id="G0", passed=True, reason="OK")


def check_g1_allowlist(dry_run: dict[str, Any]) -> GateResult:
    passed, reason = _dry_run_bool(dry_run, "allowlist_ok")
    return GateResult(gate_id="G1", passed=passed, reason=reason)


def check_g2_diff(diff: DiffMetrics) -> GateResult:
    total_lines = float(diff.added_lines + diff.deleted_lines)
    if total_lines > MAX_LINES:
        return GateResult(
            gate_id="G2",
            passed=False,
            reason=f"MAX_LINES_EXCEEDED:{total_lines:.2f}>{MAX_LINES:.2f}",
        )
    return GateResult(gate_id="G2", passed=True, reason="OK")


def check_g3_no_delete(diff: DiffMetrics) -> GateResult:
    deleted_lines = float(diff.deleted_lines)
    if deleted_lines > 0:
        return GateResult(
            gate_id="G3", passed=False, reason=f"DELETE_DETECTED:{deleted_lines:.2f}"
        )
    return GateResult(gate_id="G3", passed=True, reason="OK")


def check_g4_lockfile_deps(diff: DiffMetrics) -> GateResult:
    blocked = [
        path for path in diff.touched_files if path.endswith(LOCK_OR_DEP_PATTERNS)
    ]
    if blocked:
        return GateResult(
            gate_id="G4",
            passed=False,
            reason=f"LOCKFILE_OR_DEPS_CHANGED:{','.join(blocked)}",
        )
    return GateResult(gate_id="G4", passed=True, reason="OK")


def check_g5_commands(dry_run: dict[str, Any]) -> GateResult:
    passed, reason = _dry_run_bool(dry_run, "commands_pass")
    return GateResult(gate_id="G5", passed=passed, reason=reason)


def check_g6_dry_run_apply_match(dry_run: dict[str, Any]) -> GateResult:
    passed, reason = _dry_run_bool(dry_run, "dry_run_apply_match")
    return GateResult(gate_id="G6", passed=passed, reason=reason)


def run_gate_pipeline(
    task_id: str,
    qp: QueuePaths | None = None,
    audit: AuditLogger | None = None,
) -> List[GateResult]:
    qp = qp or QueuePaths()
    qp.ensure_dirs()

    if has_global_stop(qp):
        if audit:
            audit.append_event(
                {
                    "task_id": task_id,
                    "event": "GLOBAL_STOP_DETECTED",
                    "reason": "STOP_DETECTED",
                }
            )
        raise GateError("STOP_DETECTED")

    # allow gating only from work or pr (strict)
    st, task_dir = qp.find_task(task_id)
    if st not in (QueueState.WORK, QueueState.PR):
        raise GateError(f"GATE_NOT_ALLOWED_FROM_STATE: {st.value}")

    require_no_stop(task_dir, task_id, qp=qp, audit=audit)
    dry_run_path = require_dry_run(task_dir)
    diff_path = require_diff(task_dir)

    dry_run = _load_dry_run(dry_run_path)
    diff = _read_diff_metrics(diff_path)

    return [
        check_g0_stop(task_dir),
        check_g1_allowlist(dry_run),
        check_g2_diff(diff),
        check_g3_no_delete(diff),
        check_g4_lockfile_deps(diff),
        check_g5_commands(dry_run),
        check_g6_dry_run_apply_match(dry_run),
    ]


def gate_passed(results: List[GateResult]) -> bool:
    return all(r.passed for r in results)
