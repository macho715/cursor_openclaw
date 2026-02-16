import json
from pathlib import Path

from src.queue.audit_paths import audit_date_partition, audit_path, find_audit_logs
from src.queue.decision import decide
from src.queue.state_machine import QueuePaths, QueueState


def _mk_task(qp: QueuePaths, state: QueueState, task_id: str) -> Path:
    p = qp.task_dir(state, task_id)
    p.mkdir(parents=True, exist_ok=True)
    (p / "artifacts").mkdir(parents=True, exist_ok=True)
    return p


def _write_success_artifacts(task_dir: Path) -> None:
    (task_dir / "artifacts" / "dry_run.json").write_text(
        json.dumps(
            {
                "allowlist_ok": True,
                "commands_pass": True,
                "dry_run_apply_match": True,
            }
        ),
        encoding="utf-8",
    )
    (task_dir / "artifacts" / "diff.patch").write_text(
        "diff --git a/src/app.py b/src/app.py\n"
        "--- a/src/app.py\n"
        "+++ b/src/app.py\n"
        "+new line\n",
        encoding="utf-8",
    )


def _assert_single_fixed_audit_path(qp: QueuePaths, task_id: str) -> None:
    expected = audit_path(task_id, qp)
    assert expected.exists()
    assert expected.parent.name == audit_date_partition()

    legacy_logs = list(qp.root.glob(f"*/{task_id}/audit/audit.log.jsonl"))
    assert legacy_logs == []


def test_find_audit_logs_supports_legacy_and_partition_paths(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    qp = QueuePaths()
    qp.ensure_dirs()

    task_id = "LEGACY1"
    partitioned = audit_path(task_id, qp)
    partitioned.parent.mkdir(parents=True, exist_ok=True)
    partitioned.write_text("{}\n", encoding="utf-8")

    flat_legacy = qp.root / "audit" / f"{task_id}.jsonl"
    flat_legacy.parent.mkdir(parents=True, exist_ok=True)
    flat_legacy.write_text("{}\n", encoding="utf-8")

    nested_legacy = qp.root / "work" / task_id / "audit" / "audit.log.jsonl"
    nested_legacy.parent.mkdir(parents=True, exist_ok=True)
    nested_legacy.write_text("{}\n", encoding="utf-8")

    assert find_audit_logs(task_id, qp) == [partitioned, flat_legacy, nested_legacy]


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

    audit_log = audit_path(task_id, qp)
    event = json.loads(audit_log.read_text(encoding="utf-8").splitlines()[-1])
    assert event["reason"] == "DRY_RUN_REQUIRED"


def test_decide_zero_stop_when_any_gate_fails(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    qp = QueuePaths()
    qp.ensure_dirs()

    task_id = "TS3"
    task_dir = _mk_task(qp, QueueState.WORK, task_id)
    _write_success_artifacts(task_dir)
    (task_dir / "artifacts" / "dry_run.json").write_text(
        json.dumps(
            {
                "allowlist_ok": True,
                "commands_pass": False,
                "dry_run_apply_match": True,
            }
        ),
        encoding="utf-8",
    )

    result = decide(task_id, qp=qp)

    assert result.decision == "ZERO_STOP"
    assert result.reason == "GATE_FAILED:G5:COMMANDS_PASS_FAILED"


def test_decide_pr_only_when_all_gates_pass(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    qp = QueuePaths()
    qp.ensure_dirs()

    task_id = "TS4"
    task_dir = _mk_task(qp, QueueState.WORK, task_id)
    _write_success_artifacts(task_dir)

    result = decide(task_id, qp=qp)

    assert result.decision == "PR_ONLY"
    assert result.reason == "GATES_OK"


def test_decide_global_stop_returns_zero_stop_and_blocks(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    qp = QueuePaths()
    qp.ensure_dirs()

    task_id = "TS5"
    task_dir = _mk_task(qp, QueueState.WORK, task_id)
    _write_success_artifacts(task_dir)
    (qp.root / "STOP").write_text("STOP\n", encoding="utf-8")

    result = decide(task_id, qp=qp)

    assert result.decision == "ZERO_STOP"
    assert result.reason == "STOP_DETECTED"
    assert qp.task_dir(QueueState.BLOCKED, task_id).exists()

    audit_log = audit_path(task_id, qp)
    events = [
        json.loads(line) for line in audit_log.read_text(encoding="utf-8").splitlines()
    ]
    assert any(event["event"] == "GLOBAL_STOP_DETECTED" for event in events)
    assert events[-1]["event"] == "DECIDE"
    assert events[-1]["decision"] == "ZERO_STOP"
