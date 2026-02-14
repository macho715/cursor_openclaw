판정: **조건부(Go)** — repo가 없어도 **파일 단위 “정답 코드 세트”**를 바로 제공 가능(단, 로컬에서 `pytest`로 검증 필요).
근거: 사용자가 요구한 Stage4 Deliverables(코어/테스트/CLI)를 **정적 코드 산출**로 충족 가능(실행·적용은 사용자 환경).
다음행동: 아래 파일들을 **그대로 생성** → `python -m pytest -q` 실행 → 실패 시 로그/에러를 붙여주면 TDD 방식으로 1개씩 패치.

---

## 0) 폴더 구조

```text
src/queue/state_machine.py
src/queue/gates.py
src/queue/decision.py
src/queue/audit_logger.py
tools/cli.py
tests/test_state_transitions.py
tests/test_gate_pipeline.py
tests/test_audit_log_append_only.py
```

---

## 1) src/queue/state_machine.py

```python
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Iterable, Set


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
```

---

## 2) src/queue/audit_logger.py

```python
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


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
```

---

## 3) src/queue/gates.py

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from .state_machine import QueuePaths, QueueState, has_stop, move_task


class GateError(RuntimeError):
    pass


@dataclass(frozen=True)
class GateResult:
    gate_id: str
    passed: bool
    reason: str = ""


def task_artifacts_dir(task_dir: Path) -> Path:
    return task_dir / "artifacts"


def require_task_in_state(task_id: str, state: QueueState, qp: QueuePaths | None = None) -> Path:
    qp = qp or QueuePaths()
    st, p = qp.find_task(task_id)
    if st != state:
        raise GateError(f"INVALID_TASK_STATE: expected={state.value} actual={st.value}")
    return p


def require_no_stop(task_dir: Path, task_id: str, qp: QueuePaths | None = None) -> None:
    if has_stop(task_dir):
        qp = qp or QueuePaths()
        # best effort: move to blocked if allowed from current state
        try:
            move_task(task_id, QueueState.BLOCKED, qp=qp)
        except Exception:
            pass
        raise GateError("STOP_DETECTED")


def require_dry_run(task_dir: Path) -> Path:
    p = task_artifacts_dir(task_dir) / "dry_run.json"
    if not p.exists():
        raise GateError("DRY_RUN_REQUIRED")
    return p


def require_diff(task_dir: Path) -> Path:
    p = task_artifacts_dir(task_dir) / "diff.patch"
    if not p.exists():
        raise GateError("DIFF_REQUIRED")
    return p


def run_gate_pipeline(task_id: str, qp: QueuePaths | None = None) -> List[GateResult]:
    qp = qp or QueuePaths()
    qp.ensure_dirs()
    # allow gating only from work or pr (strict)
    st, task_dir = qp.find_task(task_id)
    if st not in (QueueState.WORK, QueueState.PR):
        raise GateError(f"GATE_NOT_ALLOWED_FROM_STATE: {st.value}")

    require_no_stop(task_dir, task_id, qp=qp)
    require_dry_run(task_dir)
    require_diff(task_dir)

    # Policy-defined G0~G6 (placeholder skeleton): pass/fail list
    results: List[GateResult] = []
    for gid in ["G0", "G1", "G2", "G3", "G4", "G5", "G6"]:
        results.append(GateResult(gate_id=gid, passed=True, reason="OK"))

    return results


def gate_passed(results: List[GateResult]) -> bool:
    return all(r.passed for r in results)
```

---

## 4) src/queue/decision.py

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Literal, Optional

from .audit_logger import AuditLogger
from .gates import GateError, gate_passed, run_gate_pipeline
from .state_machine import QueuePaths, QueueState, has_stop, move_task


DecisionType = Literal["AUTO_MERGE", "PR_ONLY", "ZERO_STOP"]


@dataclass(frozen=True)
class Decision:
    decision: DecisionType
    reason: str


def decide(task_id: str, audit: AuditLogger, qp: QueuePaths | None = None) -> Decision:
    qp = qp or QueuePaths()
    st, task_dir = qp.find_task(task_id)

    if has_stop(task_dir):
        try:
            move_task(task_id, QueueState.BLOCKED, qp=qp)
        except Exception:
            pass
        audit.append_event({"task_id": task_id, "event": "DECIDE", "decision": "ZERO_STOP", "reason": "STOP_DETECTED"})
        return Decision(decision="ZERO_STOP", reason="STOP_DETECTED")

    try:
        results = run_gate_pipeline(task_id, qp=qp)
    except GateError as e:
        # Gate entry failure is ZERO_STOP
        try:
            move_task(task_id, QueueState.BLOCKED, qp=qp)
        except Exception:
            pass
        audit.append_event({"task_id": task_id, "event": "DECIDE", "decision": "ZERO_STOP", "reason": str(e)})
        return Decision(decision="ZERO_STOP", reason=str(e))

    if not gate_passed(results):
        try:
            move_task(task_id, QueueState.BLOCKED, qp=qp)
        except Exception:
            pass
        audit.append_event({"task_id": task_id, "event": "DECIDE", "decision": "ZERO_STOP", "reason": "GATE_FAILED"})
        return Decision(decision="ZERO_STOP", reason="GATE_FAILED")

    # Stage4: never actually merge; default PR_ONLY
    audit.append_event({"task_id": task_id, "event": "DECIDE", "decision": "PR_ONLY", "reason": "GATES_OK"})
    return Decision(decision="PR_ONLY", reason="GATES_OK")
```

---

## 5) tools/cli.py

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path

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
        json.dumps([r.__dict__ for r in results], indent=2),
        encoding="utf-8",
    )
    _audit(args.task, task_dir).append_event({"task_id": args.task, "event": "GATE"})
    return 0


def cmd_decide(args: argparse.Namespace) -> int:
    qp = _qp()
    st, task_dir = qp.find_task(args.task)
    d = decide(args.task, audit=_audit(args.task, task_dir), qp=qp)
    (task_dir / "artifacts" / "decision.json").write_text(json.dumps(d.__dict__, indent=2), encoding="utf-8")
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
```

---

## 6) tests/test_state_transitions.py

```python
import pytest

from src.queue.state_machine import (
    QueueState,
    TransitionError,
    validate_transition,
    ALLOWED_TRANSITIONS,
)


def test_allowed_transitions_only():
    # all allowed transitions should pass
    for src, dsts in ALLOWED_TRANSITIONS.items():
        for dst in dsts:
            validate_transition(src, dst)

    # all disallowed transitions should fail
    all_states = list(QueueState)
    for src in all_states:
        for dst in all_states:
            if dst in ALLOWED_TRANSITIONS.get(src, set()):
                continue
            if src == dst:
                # self-transition is disallowed everywhere
                with pytest.raises(TransitionError):
                    validate_transition(src, dst)
            else:
                with pytest.raises(TransitionError):
                    validate_transition(src, dst)
```

---

## 7) tests/test_gate_pipeline.py

```python
import json
from pathlib import Path

import pytest

from src.queue.gates import GateError, run_gate_pipeline
from src.queue.state_machine import QueuePaths, QueueState


@pytest.fixture()
def qp(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    q = QueuePaths()
    q.ensure_dirs()
    return q


def _mk_task(qp: QueuePaths, state: QueueState, task_id: str) -> Path:
    p = qp.task_dir(state, task_id)
    p.mkdir(parents=True, exist_ok=True)
    (p / "artifacts").mkdir(parents=True, exist_ok=True)
    return p


def test_dry_run_required_for_gate(qp: QueuePaths):
    task_id = "T1"
    task_dir = _mk_task(qp, QueueState.WORK, task_id)
    # no dry_run.json
    with pytest.raises(GateError, match="DRY_RUN_REQUIRED"):
        run_gate_pipeline(task_id, qp=qp)


def test_diff_required_for_gate(qp: QueuePaths):
    task_id = "T2"
    task_dir = _mk_task(qp, QueueState.WORK, task_id)
    (task_dir / "artifacts" / "dry_run.json").write_text(json.dumps({"ok": True}), encoding="utf-8")
    # no diff.patch
    with pytest.raises(GateError, match="DIFF_REQUIRED"):
        run_gate_pipeline(task_id, qp=qp)


def test_gate_not_allowed_from_inbox(qp: QueuePaths):
    task_id = "T3"
    _mk_task(qp, QueueState.INBOX, task_id)
    with pytest.raises(GateError, match="GATE_NOT_ALLOWED_FROM_STATE"):
        run_gate_pipeline(task_id, qp=qp)


def test_stop_forces_block(qp: QueuePaths):
    task_id = "T4"
    task_dir = _mk_task(qp, QueueState.WORK, task_id)
    (task_dir / "STOP").write_text("STOP\n", encoding="utf-8")
    with pytest.raises(GateError, match="STOP_DETECTED"):
        run_gate_pipeline(task_id, qp=qp)

    # best-effort blocked move may or may not succeed depending on state;
    # but STOP must prevent gating.
```

---

## 8) tests/test_audit_log_append_only.py

```python
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
```

---

## 9) 로컬 실행 예시(정책 플로우)

```bash
python tools/cli.py init --task DEMO1
python tools/cli.py claim --task DEMO1
python tools/cli.py work --task DEMO1

python tools/cli.py dry-run --task DEMO1
python tools/cli.py diff --task DEMO1
python tools/cli.py gate --task DEMO1
python tools/cli.py decide --task DEMO1
python tools/cli.py apply --task DEMO1   # 실제 적용 아님: apply_request.json 패키징만
```

---

### 옵션(선택) 3가지

* **A) 그대로 사용**: 위 코드로 Stage4 핵심 요구(전이/선행조건/STOP/append-only/CLI 우회차단) 충족.
* **B) Gate(G0~G6) 실구현**: `docs/policy/TOOL_POLICY.md`를 읽어 **정확히 매핑**(지금은 placeholder pass).
* **C) 로그 보호 강화**: audit를 **단일 파일 + 해시체인 + fsync + read-only 권장 모드**로 강화(테스트 추가).

---

## CmdRec

* `/switch_mode PRIME + /logi-master report` (정책/게이트 정의를 “테스트 케이스”로 변환할 때)
* `/logi-master --deep report` (G0~G6를 정책 문서에서 1:1 코드로 내릴 때)

원하면, 다음 턴에서 **Gate(G0~G6)를 실제 정책 문서 문구 기반으로 “테스트 먼저” 재작성(TDD 큐 T0부터)**까지 바로 이어갈 수 있다.

