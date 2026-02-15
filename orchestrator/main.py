from __future__ import annotations

import argparse
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
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, Updater

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
        self.allowed_chat_ids = self._resolve_allowed_chat_ids()

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

    def _resolve_allowed_chat_ids(self) -> set[str]:
        telegram_cfg = self.config.get("telegram", {})
        allowed: set[str] = set()

        chat_id = str(telegram_cfg.get("chat_id", "")).strip()
        if chat_id:
            allowed.add(chat_id)

        extra = telegram_cfg.get("allowed_chat_ids", [])
        if isinstance(extra, list):
            allowed.update(str(x).strip() for x in extra if str(x).strip())
        return allowed

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

    def _telegram_ready(self) -> bool:
        token = str(self.config.get("telegram", {}).get("bot_token", "")).strip()
        return bool(token and not token.startswith("YOUR_"))

    def _chat_allowed(self, update: Update) -> bool:
        if not update.effective_chat:
            return False
        if not self.allowed_chat_ids:
            return True
        return str(update.effective_chat.id) in self.allowed_chat_ids

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

    def run_polling(self) -> int:
        if not self._telegram_ready():
            print("[ERR] telegram.bot_token is not configured.")
            return 1

        token = self.config["telegram"]["bot_token"]
        updater = Updater(token=token, use_context=True, workers=1)
        dispatcher = updater.dispatcher

        def start_handler(update: Update, context: CallbackContext) -> None:
            if not self._chat_allowed(update):
                return
            update.message.reply_text(
                "Orchestrator online. Use /work <instruction> to generate patch proposal."
            )

        def work_handler(update: Update, context: CallbackContext) -> None:
            if not self._chat_allowed(update):
                if update.message:
                    update.message.reply_text("Unauthorized chat.")
                return
            if not update.message:
                return

            work_text = " ".join(context.args).strip()
            if not work_text:
                update.message.reply_text("Usage: /work <instruction>")
                return

            update.message.reply_text("Accepted. Running Mode B gate pipeline...")
            code = self.process_work(work_text)
            if code == 0:
                update.message.reply_text("Done: PATCH READY (gate check PASS).")
            else:
                update.message.reply_text(f"Failed: process_work code={code}. Check report.")

        dispatcher.add_handler(CommandHandler("start", start_handler))
        dispatcher.add_handler(CommandHandler("work", work_handler, pass_args=True))

        print("[INFO] Telegram polling started. Press Ctrl+C to stop.")
        updater.start_polling(drop_pending_updates=True)
        updater.idle()
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Orchestrator MVP")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--polling", action="store_true", help="Run Telegram polling mode")
    parser.add_argument("--work-text", default="", help="Run one-shot work text")
    args = parser.parse_args()

    config_path = (Path(__file__).resolve().parent / args.config).resolve()
    orch = Orchestrator(config_path)

    polling_enabled = bool(
        args.polling or orch.config.get("telegram", {}).get("polling_enabled", False)
    )
    if polling_enabled:
        return orch.run_polling()

    work_text = args.work_text.strip()
    if not work_text:
        work_text = input("Enter /work text: ").strip()
    if not work_text:
        print("[ERR] Empty work text")
        return 1
    return orch.process_work(work_text)


if __name__ == "__main__":
    raise SystemExit(main())
