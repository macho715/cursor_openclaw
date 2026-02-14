from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure project root is on path when run as script
if __name__ == "__main__" or "pytest" not in sys.modules:
    _root = Path(__file__).resolve().parent.parent
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

from src.queue.audit_logger import AuditLogger
from src.queue.decision import decide
from src.queue.gates import run_gate_pipeline
from src.queue.state_machine import QueuePaths, QueueState, move_task


def _qp() -> QueuePaths:
    return QueuePaths()


def _audit(task_id: str, task_dir: Path) -> AuditLogger:
    # audit log per task (append-only)
    return AuditLogger(task_dir / "audit" / "audit.log.jsonl")


def ensure_task_exists(task_id: str, initial: QueueState = QueueState.INBOX) -> Path:
    qp = _qp()
    qp.ensure_dirs()
    p = qp.task_dir(initial, task_id)
    p.mkdir(parents=True, exist_ok=True)
    (p / "artifacts").mkdir(parents=True, exist_ok=True)
    return p


def cmd_dry_run(args: argparse.Namespace) -> int:
    qp = _qp()
    st, task_dir = qp.find_task(args.task)
    (task_dir / "artifacts").mkdir(parents=True, exist_ok=True)
    payload = {"task_id": args.task, "dry_run": True, "note": "snapshot-only"}
    (task_dir / "artifacts" / "dry_run.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _audit(args.task, task_dir).append_event({"task_id": args.task, "event": "DRY_RUN"})
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    qp = _qp()
    st, task_dir = qp.find_task(args.task)
    # require dry-run first
    dry = task_dir / "artifacts" / "dry_run.json"
    if not dry.exists():
        raise SystemExit("DRY_RUN_REQUIRED")
    # Stage4: only diff packaging (no apply)
    patch = "diff --git a/README.md b/README.md\n# (placeholder) no real apply in Stage4\n"
    (task_dir / "artifacts" / "diff.patch").write_text(patch, encoding="utf-8")
    _audit(args.task, task_dir).append_event({"task_id": args.task, "event": "DIFF"})
    return 0


def cmd_gate(args: argparse.Namespace) -> int:
    qp = _qp()
    results = run_gate_pipeline(args.task, qp=qp)
    st, task_dir = qp.find_task(args.task)
    (task_dir / "artifacts" / "gate.json").write_text(
        json.dumps([{"gate_id": r.gate_id, "passed": r.passed, "reason": r.reason} for r in results], indent=2),
        encoding="utf-8",
    )
    _audit(args.task, task_dir).append_event({"task_id": args.task, "event": "GATE"})
    return 0


def cmd_decide(args: argparse.Namespace) -> int:
    qp = _qp()
    st, task_dir = qp.find_task(args.task)
    d = decide(args.task, audit=_audit(args.task, task_dir), qp=qp)
    _, task_dir = qp.find_task(args.task)
    blocked_dir = qp.task_dir(QueueState.BLOCKED, args.task)
    if blocked_dir.exists():
        task_dir = blocked_dir
    artifacts_dir = task_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    (artifacts_dir / "decision.json").write_text(
        json.dumps({"decision": d.decision, "reason": d.reason}, indent=2),
        encoding="utf-8",
    )
    return 0


def cmd_apply(args: argparse.Namespace) -> int:
    """
    Stage4 constraint: never actually apply patches.
    Only package an APPLY_REQUEST bundle that Cursor(Control-Plane) can approve/run.
    """
    qp = _qp()
    st, task_dir = qp.find_task(args.task)

    # enforce: dry-run -> diff -> gate -> decision must exist
    artifacts = task_dir / "artifacts"
    required = ["dry_run.json", "diff.patch", "gate.json", "decision.json"]
    missing = [x for x in required if not (artifacts / x).exists()]
    if missing:
        raise SystemExit(f"APPLY_PRECONDITION_FAIL: missing={missing}")

    bundle = {
        "task_id": args.task,
        "mode": "APPLY_REQUEST_ONLY",
        "artifacts": required,
    }
    (artifacts / "apply_request.json").write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    _audit(args.task, task_dir).append_event({"task_id": args.task, "event": "APPLY_REQUEST_PACKAGED"})
    return 0


def cmd_block(args: argparse.Namespace) -> int:
    qp = _qp()
    st, task_dir = qp.find_task(args.task)
    _audit(args.task, task_dir).append_event({"task_id": args.task, "event": "BLOCK", "reason": args.reason})
    # move to blocked if allowed
    try:
        move_task(args.task, QueueState.BLOCKED, qp=qp)
    except Exception:
        pass
    return 0


def cmd_claim(args: argparse.Namespace) -> int:
    qp = _qp()
    move_task(args.task, QueueState.CLAIMED, qp=qp)
    st, task_dir = qp.find_task(args.task)
    _audit(args.task, task_dir).append_event({"task_id": args.task, "event": "CLAIM"})
    return 0


def cmd_work(args: argparse.Namespace) -> int:
    qp = _qp()
    move_task(args.task, QueueState.WORK, qp=qp)
    st, task_dir = qp.find_task(args.task)
    _audit(args.task, task_dir).append_event({"task_id": args.task, "event": "WORK"})
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="autodev-cli")
    sub = p.add_subparsers(dest="cmd", required=True)

    init = sub.add_parser("init")
    init.add_argument("--task", required=True)
    init.set_defaults(func=lambda a: (ensure_task_exists(a.task), 0)[1])

    claim = sub.add_parser("claim")
    claim.add_argument("--task", required=True)
    claim.set_defaults(func=cmd_claim)

    work = sub.add_parser("work")
    work.add_argument("--task", required=True)
    work.set_defaults(func=cmd_work)

    dr = sub.add_parser("dry-run")
    dr.add_argument("--task", required=True)
    dr.set_defaults(func=cmd_dry_run)

    df = sub.add_parser("diff")
    df.add_argument("--task", required=True)
    df.set_defaults(func=cmd_diff)

    gt = sub.add_parser("gate")
    gt.add_argument("--task", required=True)
    gt.set_defaults(func=cmd_gate)

    dc = sub.add_parser("decide")
    dc.add_argument("--task", required=True)
    dc.set_defaults(func=cmd_decide)

    ap = sub.add_parser("apply")
    ap.add_argument("--task", required=True)
    ap.set_defaults(func=cmd_apply)

    bl = sub.add_parser("block")
    bl.add_argument("--task", required=True)
    bl.add_argument("--reason", required=True)
    bl.set_defaults(func=cmd_block)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
