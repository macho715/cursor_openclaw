import json
from pathlib import Path

import pytest

from src.queue.gates import GateError, gate_passed, run_gate_pipeline
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


def _write_min_gate_artifacts(task_dir: Path, **dry_run_overrides: bool) -> None:
    dry_run_payload = {
        "allowlist_ok": True,
        "commands_pass": True,
        "dry_run_apply_match": True,
    }
    dry_run_payload.update(dry_run_overrides)
    (task_dir / "artifacts" / "dry_run.json").write_text(
        json.dumps(dry_run_payload), encoding="utf-8"
    )
    (task_dir / "artifacts" / "diff.patch").write_text(
        "diff --git a/src/app.py b/src/app.py\n"
        "--- a/src/app.py\n"
        "+++ b/src/app.py\n"
        "+new line\n",
        encoding="utf-8",
    )


def test_dry_run_required_for_gate(qp: QueuePaths):
    task_id = "T1"
    _mk_task(qp, QueueState.WORK, task_id)
    with pytest.raises(GateError, match="DRY_RUN_REQUIRED"):
        run_gate_pipeline(task_id, qp=qp)


def test_diff_required_for_gate(qp: QueuePaths):
    task_id = "T2"
    task_dir = _mk_task(qp, QueueState.WORK, task_id)
    (task_dir / "artifacts" / "dry_run.json").write_text(
        json.dumps({"ok": True}), encoding="utf-8"
    )
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
    _write_min_gate_artifacts(task_dir)
    with pytest.raises(GateError, match="STOP_DETECTED"):
        run_gate_pipeline(task_id, qp=qp)


def test_single_gate_failure_marks_only_target_gate(qp: QueuePaths) -> None:
    task_id = "T5"
    task_dir = _mk_task(qp, QueueState.WORK, task_id)
    _write_min_gate_artifacts(task_dir, commands_pass=False)

    results = run_gate_pipeline(task_id, qp=qp)

    failed_gate_ids = [result.gate_id for result in results if not result.passed]
    assert failed_gate_ids == ["G5"]
    assert (
        next(result for result in results if result.gate_id == "G5").reason
        == "COMMANDS_PASS_FAILED"
    )


def test_gate_passed_false_when_any_gate_fails(qp: QueuePaths) -> None:
    task_id = "T6"
    task_dir = _mk_task(qp, QueueState.WORK, task_id)
    _write_min_gate_artifacts(task_dir, dry_run_apply_match=False)

    results = run_gate_pipeline(task_id, qp=qp)

    assert gate_passed(results) is False


def test_gate_passed_true_when_all_gates_pass(qp: QueuePaths) -> None:
    task_id = "T7"
    task_dir = _mk_task(qp, QueueState.WORK, task_id)
    _write_min_gate_artifacts(task_dir)

    results = run_gate_pipeline(task_id, qp=qp)

    assert gate_passed(results) is True


def test_global_stop_fails_gate_pipeline(qp: QueuePaths) -> None:
    task_id = "T8"
    task_dir = _mk_task(qp, QueueState.WORK, task_id)
    _write_min_gate_artifacts(task_dir)
    (qp.root / "STOP").write_text("STOP\n", encoding="utf-8")

    with pytest.raises(GateError, match="STOP_DETECTED"):
        run_gate_pipeline(task_id, qp=qp)
