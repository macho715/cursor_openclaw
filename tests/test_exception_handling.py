import argparse
import json
from pathlib import Path
from typing import Any

import pytest

from src.queue.audit_logger import AuditLogger
from src.queue.decision import decide
from src.queue.gates import GateError, require_no_stop
from src.queue.state_machine import QueuePaths, QueueState, TransitionError
from tools.cli import cmd_block


@pytest.fixture()
def qp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> QueuePaths:
    monkeypatch.chdir(tmp_path)
    q = QueuePaths()
    q.ensure_dirs()
    return q


def _mk_task(qp: QueuePaths, state: QueueState, task_id: str) -> Path:
    p = qp.task_dir(state, task_id)
    p.mkdir(parents=True, exist_ok=True)
    (p / "artifacts").mkdir(parents=True, exist_ok=True)
    return p


def test_require_no_stop_handles_transition_error_and_logs_audit(
    qp: QueuePaths, monkeypatch: pytest.MonkeyPatch
) -> None:
    task_id = "T100"
    task_dir = _mk_task(qp, QueueState.WORK, task_id)
    (task_dir / "STOP").write_text("STOP\n", encoding="utf-8")
    audit = AuditLogger(task_dir / "audit" / "audit.log.jsonl")

    def _raise_transition(*args: Any, **kwargs: Any) -> None:
        raise TransitionError("INVALID_TRANSITION: work -> blocked")

    monkeypatch.setattr("src.queue.gates.move_task", _raise_transition)

    with pytest.raises(GateError, match="STOP_DETECTED"):
        require_no_stop(task_dir, task_id, qp=qp, audit=audit)

    records = [
        json.loads(line)
        for line in audit.log_path.read_text(encoding="utf-8").splitlines()
    ]
    assert records[-1]["event"] == "STOP_BLOCK_MOVE_SKIPPED"


def test_require_no_stop_surfaces_unexpected_exception(
    qp: QueuePaths, monkeypatch: pytest.MonkeyPatch
) -> None:
    task_id = "T101"
    task_dir = _mk_task(qp, QueueState.WORK, task_id)
    (task_dir / "STOP").write_text("STOP\n", encoding="utf-8")

    def _raise_value_error(*args: Any, **kwargs: Any) -> None:
        raise ValueError("unexpected")

    monkeypatch.setattr("src.queue.gates.move_task", _raise_value_error)

    with pytest.raises(ValueError, match="unexpected"):
        require_no_stop(task_dir, task_id, qp=qp)


def test_cmd_block_handles_transition_error_and_surfaces_unexpected(
    qp: QueuePaths, monkeypatch: pytest.MonkeyPatch
) -> None:
    task_id = "T102"
    task_dir = _mk_task(qp, QueueState.BLOCKED, task_id)
    args = argparse.Namespace(task=task_id, reason="manual")

    def _raise_transition(*args: Any, **kwargs: Any) -> None:
        raise TransitionError("INVALID_TRANSITION: blocked -> blocked")

    monkeypatch.setattr("tools.cli.move_task", _raise_transition)
    assert cmd_block(args) == 0

    audit_path = task_dir / "audit" / "audit.log.jsonl"
    records = [
        json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()
    ]
    assert records[-1]["event"] == "BLOCK_MOVE_SKIPPED"

    def _raise_runtime_error(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr("tools.cli.move_task", _raise_runtime_error)
    with pytest.raises(RuntimeError, match="boom"):
        cmd_block(args)


def test_decide_handles_transition_error_and_surfaces_unexpected(
    qp: QueuePaths, monkeypatch: pytest.MonkeyPatch
) -> None:
    task_id = "T103"
    task_dir = _mk_task(qp, QueueState.WORK, task_id)
    (task_dir / "STOP").write_text("STOP\n", encoding="utf-8")
    audit = AuditLogger(task_dir / "audit" / "audit.log.jsonl")

    def _raise_transition(*args: Any, **kwargs: Any) -> None:
        raise TransitionError("INVALID_TRANSITION: work -> blocked")

    monkeypatch.setattr("src.queue.decision.move_task", _raise_transition)
    decision = decide(task_id, audit=audit, qp=qp)
    assert decision.decision == "ZERO_STOP"

    records = [
        json.loads(line)
        for line in audit.log_path.read_text(encoding="utf-8").splitlines()
    ]
    assert records[-2]["event"] == "DECIDE_BLOCK_MOVE_SKIPPED"
    assert records[-1]["event"] == "DECIDE"

    def _raise_runtime_error(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr("src.queue.decision.move_task", _raise_runtime_error)
    with pytest.raises(RuntimeError, match="boom"):
        decide(task_id, audit=audit, qp=qp)
