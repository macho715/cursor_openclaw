from __future__ import annotations

import hashlib
import json
import os
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO, Dict, Iterator

if os.name == "nt":
    import msvcrt
else:
    import fcntl


class AuditLogIntegrityError(RuntimeError):
    pass


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AuditLogger:
    log_path: Path

    @contextmanager
    def _exclusive_file_lock(self) -> Iterator[BinaryIO]:
        """KR/EN: 로그 파일에 프로세스 간 배타 락을 적용합니다 / Apply cross-process exclusive lock."""
        lock_file = open(self.log_path, "a+b")
        try:
            if os.name == "nt":
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)  # type: ignore[attr-defined]
            else:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            yield lock_file
        finally:
            if os.name == "nt":
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)  # type: ignore[attr-defined]
            else:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            lock_file.close()

    def _read_lines(self) -> list[str]:
        if not self.log_path.exists():
            return []
        return self.log_path.read_text(encoding="utf-8").splitlines()

    def verify_integrity(self) -> None:
        lines = self._read_lines()
        self._verify_lines(lines)

    def _verify_lines(self, lines: list[str]) -> None:
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
            canonical = json.dumps(
                payload, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
            calc = _sha256_hex(canonical)
            if rh != calc:
                raise AuditLogIntegrityError(f"LOG_RECORD_HASH_MISMATCH@{idx}")

            prev_hash = rh

    def append_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self._exclusive_file_lock() as locked_file:
            locked_file.seek(0)
            raw_text = locked_file.read().decode("utf-8")
            lines = raw_text.splitlines()

            # verify + prev_hash compute + append is one critical section
            self._verify_lines(lines)

            prev_hash = "0" * 64
            if lines:
                prev_obj = json.loads(lines[-1])
                prev_hash = prev_obj["record_hash"]

            base = {
                "ts_utc": _utc_now_iso(),
                "prev_hash": prev_hash,
                **event,
            }
            canonical = json.dumps(base, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
            record_hash = _sha256_hex(canonical)
            row = {**base, "record_hash": record_hash}
            line = json.dumps(row, sort_keys=True, separators=(",", ":"))

            locked_file.seek(0, os.SEEK_END)
            locked_file.write((line + "\n").encode("utf-8"))
            locked_file.flush()

            return row
