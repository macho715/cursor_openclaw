import json
from pathlib import Path

import pytest

from src.queue.audit_logger import AuditLogger, AuditLogIntegrityError


def test_audit_log_append_only_detects_tamper(tmp_path: Path):
    log_path = tmp_path / "audit" / "audit.log.jsonl"
    logger = AuditLogger(log_path)

    # first append ok
    e1 = logger.append_event({"task_id": "X", "event": "ONE"})
    e2 = logger.append_event({"task_id": "X", "event": "TWO"})
    assert log_path.exists()

    # tamper: overwrite file content (simulate non-append edit)
    lines = log_path.read_text(encoding="utf-8").splitlines()
    obj0 = json.loads(lines[0])
    obj0["event"] = "HACKED"
    lines[0] = json.dumps(obj0, sort_keys=True, separators=(",", ":"))
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # next append must fail integrity
    with pytest.raises(AuditLogIntegrityError):
        logger.append_event({"task_id": "X", "event": "THREE"})
