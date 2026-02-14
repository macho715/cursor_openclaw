import json
from pathlib import Path

from src.queue.decision import decide
from src.queue.state_machine import QueuePaths, QueueState


def _mk_task(qp: QueuePaths, state: QueueState, task_id: str) -> Path:
    p = qp.task_dir(state, task_id)
    p.mkdir(parents=True, exist_ok=True)
    (p / "artifacts").mkdir(parents=True, exist_ok=True)
    return p


def _assert_single_fixed_audit_path(qp: QueuePaths, task_id: str) -> None:
    expected = qp.root / "audit" / f"{task_id}.jsonl"
    assert expected.exists()

    legacy_logs = list(qp.root.glob(f"*/{task_id}/audit/audit.log.jsonl"))
    assert legacy_logs == []


def test_decide_stop_moves_blocked_and_writes_audit_once(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    qp = QueuePaths()
    qp.ensure_dirs()

    task_id = "TS1"
    task_dir = _mk_task(qp, QueueState.WORK, task_id)
    (task_dir / "STOP").write_text("STOP\n", encoding="utf-8")

    result = decide(task_id, qp=qp)

    assert result.decision == "ZERO_STOP"
    assert result.reason == "STOP_DETECTED"
    assert qp.task_dir(QueueState.BLOCKED, task_id).exists()
    _assert_single_fixed_audit_path(qp, task_id)


def test_decide_gate_error_moves_blocked_and_writes_audit_once(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    qp = QueuePaths()
    qp.ensure_dirs()

    task_id = "TS2"
    _mk_task(qp, QueueState.WORK, task_id)

    result = decide(task_id, qp=qp)

    assert result.decision == "ZERO_STOP"
    assert result.reason == "DRY_RUN_REQUIRED"
    assert qp.task_dir(QueueState.BLOCKED, task_id).exists()
    _assert_single_fixed_audit_path(qp, task_id)

    audit_log = qp.root / "audit" / f"{task_id}.jsonl"
    event = json.loads(audit_log.read_text(encoding="utf-8").splitlines()[-1])
    assert event["reason"] == "DRY_RUN_REQUIRED"
