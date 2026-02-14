import json
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from src.queue.audit_logger import AuditLogger, AuditLogIntegrityError


def _append_in_process(log_path: str, process_id: int, count: int) -> None:
    logger = AuditLogger(Path(log_path))
    for idx in range(count):
        logger.append_event(
            {
                "task_id": f"P{process_id}",
                "event": "PROCESS_APPEND",
                "idx": idx,
            }
        )


def test_audit_log_append_only_detects_tamper(tmp_path: Path) -> None:
    log_path = tmp_path / "audit" / "audit.log.jsonl"
    logger = AuditLogger(log_path)

    # first append ok
    logger.append_event({"task_id": "X", "event": "ONE"})
    logger.append_event({"task_id": "X", "event": "TWO"})
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


def test_audit_log_integrity_with_concurrent_threads(tmp_path: Path) -> None:
    log_path = tmp_path / "audit" / "threaded_audit.log.jsonl"
    logger = AuditLogger(log_path)

    workers = 8
    per_worker = 20

    def _append_in_thread(thread_id: int) -> None:
        for idx in range(per_worker):
            logger.append_event(
                {
                    "task_id": f"T{thread_id}",
                    "event": "THREAD_APPEND",
                    "idx": idx,
                }
            )

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(_append_in_thread, thread_id)
            for thread_id in range(workers)
        ]
        for future in futures:
            future.result()

    logger.verify_integrity()
    assert (
        len(log_path.read_text(encoding="utf-8").splitlines()) == workers * per_worker
    )


def test_audit_log_integrity_with_concurrent_processes(tmp_path: Path) -> None:
    log_path = tmp_path / "audit" / "process_audit.log.jsonl"

    processes = 4
    per_process = 25

    process_list: list[mp.Process] = []
    for process_id in range(processes):
        process = mp.Process(
            target=_append_in_process,
            args=(str(log_path), process_id, per_process),
        )
        process.start()
        process_list.append(process)

    for process in process_list:
        process.join(timeout=30)
        assert process.exitcode == 0

    logger = AuditLogger(log_path)
    logger.verify_integrity()
    assert (
        len(log_path.read_text(encoding="utf-8").splitlines())
        == processes * per_process
    )
