from __future__ import annotations

import json
import os
import shlex
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib import parse, request

import yaml

from utils.git_gate import apply_check, is_repo_clean


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    patch_dir: Path
    report_dir: Path
    prompt_template: Path


class Orchestrator:
    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path.resolve()
        self.base_dir = self.config_path.parent
        self.config = self._load_config(self.config_path)
        self.paths = self._resolve_paths(self.config)

    def _load_config(self, config_path: Path) -> dict[str, Any]:
        with config_path.open("r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        if not isinstance(cfg, dict):
            raise ValueError("config.yaml must be a mapping")

        # Environment overrides for secrets and paths
        token = os.getenv("ORCH_TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("ORCH_TELEGRAM_CHAT_ID")
        repo = os.getenv("ORCH_REPO_ROOT")
        if token:
            cfg.setdefault("telegram", {})["bot_token"] = token
        if chat_id:
            cfg.setdefault("telegram", {})["chat_id"] = chat_id
        if repo:
            cfg.setdefault("repository", {})["root_path"] = repo

        return cfg

    def _resolve_paths(self, cfg: dict[str, Any]) -> Paths:
        repo_root = Path(cfg["repository"]["root_path"]).expanduser().resolve()
        settings = cfg["settings"]
        claude = cfg["claude"]

        patch_dir = (self.base_dir / settings["patch_dir"]).resolve()
        report_dir = (self.base_dir / settings["report_dir"]).resolve()
        prompt_template = (self.base_dir / claude["prompt_template_path"]).resolve()

        patch_dir.mkdir(parents=True, exist_ok=True)
        report_dir.mkdir(parents=True, exist_ok=True)

        return Paths(
            repo_root=repo_root,
            patch_dir=patch_dir,
            report_dir=report_dir,
            prompt_template=prompt_template,
        )

    def _send_telegram(self, message: str) -> None:
        token = self.config["telegram"]["bot_token"]
        chat_id = self.config["telegram"]["chat_id"]
        if token.startswith("YOUR_") or chat_id.startswith("YOUR_"):
            print("[WARN] Telegram token/chat_id placeholders are still set; skipping send.")
            return

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        body = parse.urlencode({"chat_id": chat_id, "text": message}).encode("utf-8")
        req = request.Request(url, data=body, method="POST")
        with request.urlopen(req, timeout=20) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Telegram send failed: HTTP {resp.status}")

    def _make_task_id(self) -> str:
        prefix = self.config.get("settings", {}).get("task_prefix", "T{date}")
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return prefix.replace("{date}", stamp)

    def _render_prompt(self, work_text: str) -> str:
        template = self.paths.prompt_template.read_text(encoding="utf-8")
        return template.replace("{WORK_TEXT}", work_text)

    def _call_model(self, prompt: str) -> subprocess.CompletedProcess[str]:
        command = self.config["claude"]["ollama_command"]
        cmd_parts = shlex.split(command)
        # command should end with -p so prompt can be appended safely as one arg
        cmd_parts.append(prompt)
        return subprocess.run(
            cmd_parts,
            cwd=self.paths.repo_root,
            capture_output=True,
            text=True,
            check=False,
        )

    def process_work(self, work_text: str) -> int:
        if not is_repo_clean(self.paths.repo_root):
            self._send_telegram(
                "Repo is dirty (git status not clean). Aborting.\n"
                "Run git status and clean/stash first."
            )
            return 2

        task_id = self._make_task_id()
        patch_path = self.paths.patch_dir / f"{task_id}.patch"
        report_path = self.paths.report_dir / f"{task_id}.json"

        prompt = self._render_prompt(work_text)
        model_result = self._call_model(prompt)

        if model_result.returncode != 0:
            msg = (model_result.stderr or model_result.stdout).strip()
            self._send_telegram(f"Claude call failed: {msg[:400]}")
            report = {
                "task_id": task_id,
                "status": "MODEL_CALL_FAIL",
                "error": msg,
                "timestamp": datetime.now().isoformat(),
            }
            report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            return 3

        diff_content = model_result.stdout.strip()
        if not diff_content.startswith("diff --git a/"):
            self._send_telegram("Output is not a valid unified diff. Manual review required.")
            report = {
                "task_id": task_id,
                "status": "INVALID_DIFF",
                "preview": diff_content[:600],
                "timestamp": datetime.now().isoformat(),
            }
            report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            return 4

        patch_path.write_text(diff_content + "\n", encoding="utf-8")

        ok, error_msg = apply_check(self.paths.repo_root, patch_path)
        report = {
            "task_id": task_id,
            "work_text": work_text,
            "patch_file": patch_path.name,
            "git_apply_check": "PASS" if ok else "FAIL",
            "error_msg": error_msg if not ok else None,
            "timestamp": datetime.now().isoformat(),
        }
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        if ok:
            self._send_telegram(
                "PATCH READY\n"
                f"Task: {task_id}\n"
                f"patch: {patch_path.name}\n"
                "Apply only from Cursor control-plane after review."
            )
            print(f"[OK] Patch ready: {patch_path}")
            return 0

        self._send_telegram(
            "PATCH CHECK FAILED\n"
            f"Task: {task_id}\n"
            f"Error: {error_msg[:300]}"
        )
        print(f"[FAIL] Patch check failed: {error_msg}")
        return 5


def main() -> int:
    config_path = Path(__file__).resolve().parent / "config.yaml"
    orch = Orchestrator(config_path)
    work_text = input("Enter /work text: ").strip()
    if not work_text:
        print("[ERR] Empty work text")
        return 1
    return orch.process_work(work_text)


if __name__ == "__main__":
    raise SystemExit(main())
