import os
import json
import time
import hashlib
import shutil
from pathlib import Path
import requests
from datetime import datetime, timezone


def now_rfc3339() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", errors="ignore")).hexdigest()


def safe_read_text(path: Path, max_bytes: int) -> str:
    data = path.read_bytes()
    return data[:max_bytes].decode("utf-8", errors="replace")


def write_ndjson(audit_file: Path, event: dict) -> None:
    audit_file.parent.mkdir(parents=True, exist_ok=True)
    with audit_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def load_ssot(ssot_dir: Path) -> dict:
    manifest = json.loads((ssot_dir / "MANIFEST.json").read_text(encoding="utf-8"))
    return manifest


def stop_detected(queue_dir: Path) -> bool:
    return (queue_dir / "STOP").exists()


def claim_one_task(queue_dir: Path) -> Path | None:
    inbox = queue_dir / "inbox"
    claimed = queue_dir / "claimed"
    inbox.mkdir(parents=True, exist_ok=True)
    claimed.mkdir(parents=True, exist_ok=True)

    tasks = sorted(inbox.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if not tasks:
        return None

    src = tasks[0]
    dst = claimed / src.name
    try:
        src.rename(dst)
        return dst
    except Exception:
        return None


def build_prompt(
    system_prompt: str,
    task: dict,
    repo_dir: Path,
    max_files: int,
    max_file_bytes: int,
) -> str:
    scope = task.get("scope", {})
    target_files = scope.get("target_files", [])
    allow_patch = set(scope.get("allow_patch_on_files", []))

    ctx_files = []
    for rel in target_files[:max_files]:
        p = repo_dir / rel
        if p.exists() and p.is_file():
            ctx_files.append(rel)

    parts = []
    parts.append(system_prompt.strip())
    parts.append("\n[task_json]\n" + json.dumps(task, ensure_ascii=False, indent=2))
    parts.append("\n[repo_context]\n")

    for rel in ctx_files:
        p = repo_dir / rel
        content = safe_read_text(p, max_file_bytes)
        parts.append(f"\n---FILE:{rel}---\n{content}\n---END_FILE---\n")

    parts.append("\n[constraints]\n")
    parts.append(f"- allow_patch_on_files: {sorted(list(allow_patch))}\n")
    parts.append("- 반드시 allowlist 파일만 수정하고 unified diff로 출력할 것.\n")

    return "\n".join(parts)


def call_ollama_generate(base_url: str, model: str, prompt: str) -> str:
    url = base_url.rstrip("/") + "/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    r = requests.post(url, json=payload, timeout=600)
    r.raise_for_status()
    data = r.json()
    return data.get("response", "")


def extract_blocks(text: str) -> tuple[str, str]:
    def between(a: str, b: str) -> str:
        if a not in text or b not in text:
            return ""
        return text.split(a, 1)[1].split(b, 1)[0].strip("\n")

    patch = between("---BEGIN_PATCH---", "---END_PATCH---")
    notes = between("---BEGIN_NOTES---", "---END_NOTES---")
    return patch, notes


def main():
    queue_dir = Path(os.getenv("QUEUE_DIR", "/queue"))
    repo_dir = Path(os.getenv("REPO_DIR", "/repo"))
    ssot_dir = Path(os.getenv("SSOT_DIR", "/ssot"))
    poll_seconds = int(os.getenv("POLL_SECONDS", "2"))
    dry_run = os.getenv("DRY_RUN", "1") == "1"

    max_file_bytes = int(os.getenv("MAX_FILE_BYTES", "120000"))
    max_context_files = int(os.getenv("MAX_CONTEXT_FILES", "8"))

    base_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")

    audit_file = queue_dir / "audit" / "events.ndjson"
    work_dir = queue_dir / "work"
    blocked_dir = queue_dir / "blocked"
    work_dir.mkdir(parents=True, exist_ok=True)
    blocked_dir.mkdir(parents=True, exist_ok=True)

    system_prompt_path = Path("/app/prompts/patch_system.txt")
    system_prompt = system_prompt_path.read_text(encoding="utf-8")

    manifest = load_ssot(ssot_dir)
    repo_ref = "UNKNOWN"

    while True:
        if stop_detected(queue_dir):
            write_ndjson(
                audit_file,
                {
                    "ts": now_rfc3339(),
                    "level": "WARN",
                    "actor": "system",
                    "action": "STOP_DETECTED",
                    "task_id": "-",
                    "repo_ref": repo_ref,
                    "inputs_sha256": sha256_text("STOP"),
                    "outputs_sha256": sha256_text("STOP"),
                    "meta": {"note": "Kill-switch file exists. Worker is idling."},
                },
            )
            time.sleep(max(poll_seconds, 5))
            continue

        task_path = claim_one_task(queue_dir)
        if task_path is None:
            time.sleep(poll_seconds)
            continue

        try:
            task = json.loads(task_path.read_text(encoding="utf-8"))
        except Exception as e:
            dst = blocked_dir / task_path.name
            shutil.move(str(task_path), str(dst))
            write_ndjson(
                audit_file,
                {
                    "ts": now_rfc3339(),
                    "level": "ERROR",
                    "actor": "openclaw",
                    "action": "TASK_BLOCKED",
                    "task_id": "UNKNOWN",
                    "repo_ref": repo_ref,
                    "inputs_sha256": sha256_text(str(e)),
                    "outputs_sha256": sha256_text("blocked"),
                    "meta": {
                        "reason": "invalid_json",
                        "error": str(e),
                        "path": dst.as_posix(),
                    },
                },
            )
            continue

        task_id = task.get("task_id", Path(task_path.name).stem)

        write_ndjson(
            audit_file,
            {
                "ts": now_rfc3339(),
                "level": "INFO",
                "actor": "openclaw",
                "action": "TASK_CLAIMED",
                "task_id": task_id,
                "repo_ref": repo_ref,
                "inputs_sha256": sha256_text(task_path.read_text(encoding="utf-8")),
                "outputs_sha256": sha256_text("claimed"),
                "meta": {"dry_run": dry_run, "model": model},
            },
        )

        prompt = build_prompt(
            system_prompt=system_prompt,
            task=task,
            repo_dir=repo_dir,
            max_files=max_context_files,
            max_file_bytes=max_file_bytes,
        )
        prompt_hash = sha256_text(prompt)

        try:
            llm_text = call_ollama_generate(base_url=base_url, model=model, prompt=prompt)
        except Exception as e:
            dst = blocked_dir / f"{task_id}.json"
            shutil.move(str(task_path), str(dst))
            write_ndjson(
                audit_file,
                {
                    "ts": now_rfc3339(),
                    "level": "ERROR",
                    "actor": "openclaw",
                    "action": "ERROR",
                    "task_id": task_id,
                    "repo_ref": repo_ref,
                    "inputs_sha256": prompt_hash,
                    "outputs_sha256": sha256_text(str(e)),
                    "meta": {"reason": "ollama_call_failed", "error": str(e)},
                },
            )
            continue

        patch, notes = extract_blocks(llm_text)

        status = "PROPOSED"
        if patch.strip().startswith("# NEED_INPUT") or patch.strip() == "":
            status = "NEED_INPUT"

        patch_path = work_dir / f"{task_id}.patch"
        report_path = work_dir / f"{task_id}.report.json"

        patch_path.write_text(patch + "\n", encoding="utf-8")
        report = {
            "task_id": task_id,
            "status": status,
            "model": model,
            "dry_run": dry_run,
            "summary": notes.strip(),
            "artifacts": {"patch": patch_path.as_posix()},
            "next_actions": [
                "Cursor에서 patch 검토",
                "Gate 실행: scripts/gate_local.sh",
                "git apply 후 테스트/커밋",
            ],
            "ssot": {
                "schema_version": manifest.get("schema_version"),
                "guardrails": manifest.get("guardrails", {}),
            },
        }
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        outputs_hash = sha256_text((patch or "") + "\n" + (notes or ""))
        write_ndjson(
            audit_file,
            {
                "ts": now_rfc3339(),
                "level": "INFO" if status == "PROPOSED" else "WARN",
                "actor": "openclaw",
                "action": "PATCH_PROPOSED",
                "task_id": task_id,
                "repo_ref": repo_ref,
                "inputs_sha256": prompt_hash,
                "outputs_sha256": outputs_hash,
                "meta": {
                    "status": status,
                    "patch_path": patch_path.as_posix(),
                    "report_path": report_path.as_posix(),
                },
            },
        )

        time.sleep(0.2)


if __name__ == "__main__":
    main()
