import json
from pathlib import Path

import pytest

from src.queue.gates import GateError, run_gate_pipeline
from src.queue.state_machine import QueuePaths, QueueState


@pytest.fixture()
def qp(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    q = QueuePaths()
    q.ensure_dirs()
    return q


def _mk_task(qp: QueuePaths, state: QueueState, task_id: str) -> Path:
    p = qp.task_dir(state, task_id)
    p.mkdir(parents=True, exist_ok=True)
    (p / "artifacts").mkdir(parents=True, exist_ok=True)
    return p


def test_dry_run_required_for_gate(qp: QueuePaths):
    task_id = "T1"
    task_dir = _mk_task(qp, QueueState.WORK, task_id)
    # no dry_run.json
    with pytest.raises(GateError, match="DRY_RUN_REQUIRED"):
        run_gate_pipeline(task_id, qp=qp)


def test_diff_required_for_gate(qp: QueuePaths):
    task_id = "T2"
    task_dir = _mk_task(qp, QueueState.WORK, task_id)
    (task_dir / "artifacts" / "dry_run.json").write_text(json.dumps({"ok": True}), encoding="utf-8")
    # no diff.patch
    with pytest.raises(GateError, match="DIFF_REQUIRED"):
        run_gate_pipeline(task_id, qp=qp)


def test_gate_not_allowed_from_inbox(qp: QueuePaths):
    task_id = "T3"
    _mk_task(qp, QueueState.INBOX, task_id)
    with pytest.raises(GateError, match="GATE_NOT_ALLOWED_FROM_STATE"):
        run_gate_pipeline(task_id, qp=qp)


def test_stop_forces_block(qp: QueuePaths):
    task_id = "T4"
    task_dir = _mk_task(qp, QueueState.WORK, task_id)
    (task_dir / "STOP").write_text("STOP\n", encoding="utf-8")
    (task_dir / "artifacts" / "dry_run.json").write_text(json.dumps({"ok": True}), encoding="utf-8")
    (task_dir / "artifacts" / "diff.patch").write_text("diff\n", encoding="utf-8")
    with pytest.raises(GateError, match="STOP_DETECTED"):
        run_gate_pipeline(task_id, qp=qp)
