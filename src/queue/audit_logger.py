from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


class AuditLogIntegrityError(RuntimeError):
    pass


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AuditLogger:
    log_path: Path

    def _read_lines(self) -> list[str]:
        if not self.log_path.exists():
            return []
        return self.log_path.read_text(encoding="utf-8").splitlines()

    def verify_integrity(self) -> None:
        lines = self._read_lines()
        prev_hash = "0" * 64
        for idx, line in enumerate(lines):
            try:
                obj = json.loads(line)
            except Exception as e:
                raise AuditLogIntegrityError(f"LOG_JSON_PARSE_FAIL@{idx}: {e}") from e

            if obj.get("prev_hash") != prev_hash:
                raise AuditLogIntegrityError(f"LOG_CHAIN_BROKEN@{idx}")

            # recompute record_hash over canonical payload excluding record_hash
            payload = dict(obj)
            rh = payload.pop("record_hash", None)
            canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
            calc = _sha256_hex(canonical)
            if rh != calc:
                raise AuditLogIntegrityError(f"LOG_RECORD_HASH_MISMATCH@{idx}")

            prev_hash = rh

    def append_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        # fail fast on tamper
        self.verify_integrity()

        lines = self._read_lines()
        prev_hash = "0" * 64
        if lines:
            prev_obj = json.loads(lines[-1])
            prev_hash = prev_obj["record_hash"]

        base = {
            "ts_utc": _utc_now_iso(),
            "prev_hash": prev_hash,
            **event,
        }
        canonical = json.dumps(base, sort_keys=True, separators=(",", ":")).encode("utf-8")
        record_hash = _sha256_hex(canonical)
        row = {**base, "record_hash": record_hash}
        line = json.dumps(row, sort_keys=True, separators=(",", ":"))

        # OS-level append (best effort)
        fd = os.open(str(self.log_path), os.O_CREAT | os.O_WRONLY | os.O_APPEND, 0o644)
        try:
            os.write(fd, (line + "\n").encode("utf-8"))
        finally:
            os.close(fd)

        return row
