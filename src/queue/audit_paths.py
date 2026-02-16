from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from .state_machine import QueuePaths


def audit_date_partition(now: datetime | None = None) -> str:
    """KR/EN: 감사로그 날짜 파티션(UTC)을 계산합니다 / Compute UTC date partition for audit logs."""
    base = now.astimezone(UTC) if now is not None else datetime.now(UTC)
    return base.strftime("%Y-%m-%d")


def audit_path(task_id: str, qp: QueuePaths, now: datetime | None = None) -> Path:
    """KR/EN: 표준 감사로그 경로를 생성합니다 / Build canonical audit log path."""
    return qp.root / "audit" / audit_date_partition(now) / f"{task_id}.jsonl"


def find_audit_logs(task_id: str, qp: QueuePaths) -> list[Path]:
    """KR/EN: 신/구 경로를 함께 탐색합니다 / Discover audit logs across new and legacy paths."""
    candidates: list[Path] = []

    date_partition_logs = sorted((qp.root / "audit").glob(f"*/{task_id}.jsonl"))
    candidates.extend([p for p in date_partition_logs if p.is_file()])

    flat_legacy = qp.root / "audit" / f"{task_id}.jsonl"
    if flat_legacy.is_file():
        candidates.append(flat_legacy)

    nested_legacy = sorted(qp.root.glob(f"*/{task_id}/audit/audit.log.jsonl"))
    candidates.extend([p for p in nested_legacy if p.is_file()])

    return candidates
