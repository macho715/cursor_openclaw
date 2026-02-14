from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Set


class QueueState(str, Enum):
    INBOX = "inbox"
    CLAIMED = "claimed"
    WORK = "work"
    PR = "pr"
    DONE = "done"
    BLOCKED = "blocked"


ALLOWED_TRANSITIONS: Dict[QueueState, Set[QueueState]] = {
    QueueState.INBOX: {QueueState.CLAIMED, QueueState.BLOCKED},
    QueueState.CLAIMED: {QueueState.WORK, QueueState.BLOCKED},
    QueueState.WORK: {QueueState.PR, QueueState.BLOCKED},
    QueueState.PR: {QueueState.DONE, QueueState.BLOCKED},
    QueueState.DONE: set(),
    QueueState.BLOCKED: set(),
}


class TransitionError(RuntimeError):
    pass


@dataclass(frozen=True)
class QueuePaths:
    root: Path = Path(".autodev_queue")

    def state_dir(self, state: QueueState) -> Path:
        return self.root / state.value

    def task_dir(self, state: QueueState, task_id: str) -> Path:
        return self.state_dir(state) / task_id

    def find_task(self, task_id: str) -> tuple[QueueState, Path]:
        for st in QueueState:
            p = self.task_dir(st, task_id)
            if p.exists():
                return st, p
        raise FileNotFoundError(f"TASK_NOT_FOUND: {task_id}")

    def ensure_dirs(self) -> None:
        for st in QueueState:
            self.state_dir(st).mkdir(parents=True, exist_ok=True)


def validate_transition(src: QueueState, dst: QueueState) -> None:
    allowed = ALLOWED_TRANSITIONS.get(src, set())
    if dst not in allowed:
        raise TransitionError(f"INVALID_TRANSITION: {src.value} -> {dst.value}")


def move_task(task_id: str, dst: QueueState, qp: QueuePaths | None = None) -> Path:
    qp = qp or QueuePaths()
    qp.ensure_dirs()
    src_state, src_dir = qp.find_task(task_id)
    validate_transition(src_state, dst)
    dst_dir = qp.task_dir(dst, task_id)
    if dst_dir.exists():
        raise TransitionError(f"DST_ALREADY_EXISTS: {dst_dir}")
    src_dir.parent.mkdir(parents=True, exist_ok=True)
    dst_dir.parent.mkdir(parents=True, exist_ok=True)
    return src_dir.rename(dst_dir)


def touch_stop_flag(task_dir: Path) -> None:
    (task_dir / "STOP").write_text("STOP\n", encoding="utf-8")


def has_stop(task_dir: Path) -> bool:
    return (task_dir / "STOP").exists()
