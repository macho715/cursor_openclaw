import argparse
import json
from pathlib import Path

import pytest

from tools.cli import cmd_decide
from src.queue.state_machine import QueuePaths, QueueState


@pytest.fixture()
def qp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> QueuePaths:
    monkeypatch.chdir(tmp_path)
    queue_paths = QueuePaths()
    queue_paths.ensure_dirs()
    return queue_paths


def _mk_task(qp: QueuePaths, state: QueueState, task_id: str) -> Path:
    task_dir = qp.task_dir(state, task_id)
    task_dir.mkdir(parents=True, exist_ok=True)
    return task_dir


def test_cmd_decide_writes_decision_to_blocked_artifacts_when_stop_exists(qp: QueuePaths) -> None:
    task_id = "STOP-CASE"
    task_dir = _mk_task(qp, QueueState.WORK, task_id)
    (task_dir / "STOP").write_text("STOP\n", encoding="utf-8")

    rc = cmd_decide(argparse.Namespace(task=task_id))

    assert rc == 0
    blocked_decision = qp.task_dir(QueueState.BLOCKED, task_id) / "artifacts" / "decision.json"
    assert blocked_decision.exists()
    payload = json.loads(blocked_decision.read_text(encoding="utf-8"))
    assert payload["decision"] == "ZERO_STOP"


def test_cmd_decide_writes_decision_to_blocked_artifacts_when_gate_fails(qp: QueuePaths) -> None:
    task_id = "GATE-FAIL-CASE"
    _mk_task(qp, QueueState.WORK, task_id)

    rc = cmd_decide(argparse.Namespace(task=task_id))

    assert rc == 0
    blocked_decision = qp.task_dir(QueueState.BLOCKED, task_id) / "artifacts" / "decision.json"
    assert blocked_decision.exists()
    payload = json.loads(blocked_decision.read_text(encoding="utf-8"))
    assert payload["decision"] == "ZERO_STOP"
    assert payload["reason"] == "DRY_RUN_REQUIRED"
