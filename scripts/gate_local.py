from __future__ import annotations

import fnmatch
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SECRET_PATTERNS = (
    "BEGIN PRIVATE KEY",
    "AKIA",
    "SECRET_KEY",
    "api_key",
    "token=",
)


def now_rfc3339() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_touched_files(patch_text: str) -> list[str]:
    touched: list[str] = []
    for line in patch_text.splitlines():
        if line.startswith("+++ b/"):
            rel = line.removeprefix("+++ b/").strip()
            if rel and rel != "/dev/null":
                touched.append(rel)
    return touched


def load_json(path: str | None) -> dict:
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def check_git_apply(patch: Path) -> tuple[bool, str]:
    proc = subprocess.run(
        ["git", "apply", "--check", str(patch)],
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        return True, "OK"
    detail = (proc.stderr or proc.stdout).strip().splitlines()
    msg = detail[0] if detail else "git apply --check failed"
    return False, f"GIT_APPLY_INVALID:{msg}"


def append_gate_event(event: dict) -> None:
    audit = Path(".autodev_queue/audit/events.ndjson")
    audit.parent.mkdir(parents=True, exist_ok=True)
    with audit.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def main() -> int:
    patch_arg = sys.argv[1] if len(sys.argv) > 1 else ""
    task_arg = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else ""
    report_arg = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else ""

    if not patch_arg:
        print("[ERR] usage: gate_local.py <patch> [task_json] [report_json]")
        return 1

    patch_path = Path(patch_arg)
    if not patch_path.exists():
        print(f"[ERR] patch not found: {patch_path}")
        return 1

    patch_text = patch_path.read_text(encoding="utf-8", errors="replace")
    task = load_json(task_arg)
    report = load_json(report_arg)

    task_id = task.get("task_id", patch_path.stem)
    touched = parse_touched_files(patch_text)

    fail_code = ""
    fail_detail = ""

    if not ("+++ " in patch_text and "--- " in patch_text):
        fail_code = "UNIFIED_DIFF_HEADER_MISSING"
        fail_detail = "missing +++/--- headers"

    if not fail_code:
        for token in SECRET_PATTERNS:
            if token.lower() in patch_text.lower():
                fail_code = "SECRET_PATTERN_DETECTED"
                fail_detail = token
                break

    scope = task.get("scope", {})
    allow_patch = set(scope.get("allow_patch_on_files", []))
    deny_globs = list(scope.get("deny_paths_glob", []))

    if not fail_code and allow_patch:
        outside = [p for p in touched if p not in allow_patch]
        if outside:
            fail_code = "ALLOWLIST_VIOLATION"
            fail_detail = ",".join(outside)

    if not fail_code and deny_globs:
        denied = [
            p
            for p in touched
            if any(fnmatch.fnmatch(p, pat) or fnmatch.fnmatch(f"./{p}", pat) for pat in deny_globs)
        ]
        if denied:
            fail_code = "DENYLIST_MATCH"
            fail_detail = ",".join(denied)

    if not fail_code:
        ok, reason = check_git_apply(patch_path)
        if not ok:
            fail_code = "PATCH_NOT_APPLICABLE"
            fail_detail = reason

    tests_required = task.get("requirements", {}).get("tests", [])
    if not fail_code and tests_required:
        evidence = report.get("test_evidence") or report.get("tests")
        if not evidence:
            fail_code = "TEST_EVIDENCE_MISSING"
            fail_detail = "task requires tests but report has no test evidence"

    status = "PASS" if not fail_code else "FAIL"
    reason_code = "OK" if status == "PASS" else fail_code
    result = {
        "task_id": task_id,
        "status": status,
        "reason_code": reason_code,
        "reason_detail": fail_detail,
        "patch": str(patch_path),
        "touched_files": touched,
        "checked_at": now_rfc3339(),
    }

    gate_out = patch_path.with_suffix(".gate.json")
    gate_out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    append_gate_event(
        {
            "ts": now_rfc3339(),
            "level": "INFO" if status == "PASS" else "ERROR",
            "actor": "cursor",
            "action": "GATE_LOCAL",
            "task_id": task_id,
            "repo_ref": "LOCAL_WORKTREE",
            "inputs_sha256": "",
            "outputs_sha256": "",
            "meta": {
                "status": status,
                "reason_code": reason_code,
                "gate_report": str(gate_out),
            },
        }
    )

    if status == "PASS":
        print(f"[PASS] gate checks passed ({reason_code})")
        print(f"[INFO] touched_files={','.join(touched) if touched else '(none)'}")
        print(f"[INFO] report={gate_out}")
        return 0

    print(f"[FAIL] {reason_code}: {fail_detail}")
    print(f"[INFO] touched_files={','.join(touched) if touched else '(none)'}")
    print(f"[INFO] report={gate_out}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
