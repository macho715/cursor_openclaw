#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoDev Telegram Orchestrator (Mode B) — 2단 승인(무인→사람)

- 입력: Telegram `/work <텍스트>` (작업 요청)
- 처리: Claude Code(Ollama)로 unified diff 제안 생성 → 로컬 Gate(`git apply --check`) → report/audit 기록 → Telegram PASS/FAIL 전송
- 승인: Telegram `/approve <task_id>` 또는 `/approve`(마지막 PASS 작업) → **승인 플래그만 생성**
- 집행: Cursor에서만 `git apply` / commit / push 수행

원칙:
- 자동은 "제안/검증/리포트/승인플래그"까지만
- apply/commit/push는 절대 자동 실행하지 않음 (사람 승인 + Cursor에서 수동 실행)

보안:
- TG 토큰은 .env에만 저장(커밋 금지)
- allowlist/denylist 기반으로 touched files 통제
"""
from __future__ import annotations

import json
import os
import sys
import time
import subprocess
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]


def _utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_env(env_path: Path) -> None:
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_dirs(paths: List[Path]) -> None:
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)


def sha256_text(s: str) -> str:
    import hashlib
    return hashlib.sha256(s.encode("utf-8", errors="replace")).hexdigest()


def http_post_form(url: str, data: Dict[str, Any], timeout: int = 20) -> Dict[str, Any]:
    body = urllib.parse.urlencode({k: str(v) for k, v in data.items()}).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    return json.loads(raw)


def http_get(url: str, params: Dict[str, Any], timeout: int = 35) -> Dict[str, Any]:
    qs = urllib.parse.urlencode({k: str(v) for k, v in params.items()})
    full = url + ("?" + qs if qs else "")
    with urllib.request.urlopen(full, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    return json.loads(raw)


@dataclass
class Cfg:
    repo_root: Path
    tz: str
    tg_token: str
    allowed_chat_ids: List[int]
    work_cmd: str
    status_cmd: str
    stop_cmd: str
    resume_cmd: str
    help_cmd: str
    approve_cmd: str
    reject_cmd: str

    poll_timeout: int
    poll_interval: int
    reply_rate_limit: int
    reply_max_chars: int

    engine: str
    fallback_openclaw: bool
    openclaw_wait_sec: int
    auto_stash_policy: str

    tests_enabled: bool
    tests_cmd: str
    tests_timeout: int

    anthropic_base_url: str
    model_primary: str
    model_fallbacks: List[str]
    ollama_launch_cmd: List[str]
    prompt_template: List[str]

    allowlist: List[str]
    denylist: List[str]

    q_root: Path
    q_inbox: Path
    q_work: Path
    q_blocked: Path
    q_audit: Path
    q_approved: Path
    killswitch: Path

    patch_dir: Path
    reports_dir: Path
    runtime_dir: Path

    max_patch_bytes: int
    max_report_bytes: int

    require_clean_porcelain2: bool
    require_git_apply_check: bool
    deny_new_files: bool
    deny_binary_patches: bool

    tmpl_stop_repo_dirty: str
    tmpl_stop_killswitch: str
    tmpl_help: str
    tmpl_pass_patch_ready: str
    tmpl_fail_patch_invalid: str
    tmpl_pass_approved: str
    tmpl_fail_approve: str


def glob_match(path: str, patterns: List[str]) -> bool:
    """운영 목적의 최소 glob 매칭(**, *)"""
    from fnmatch import fnmatch
    p = path.replace("\\", "/")
    for pat in patterns:
        if fnmatch(p, pat.replace("\\", "/")):
            return True
    return False


def parse_touched_files_from_patch(patch_text: str) -> List[str]:
    files: List[str] = []
    for line in patch_text.splitlines():
        if line.startswith("+++ b/"):
            f = line[len("+++ b/"):].strip()
            if f and f != "/dev/null":
                files.append(f)
    seen = set()
    out = []
    for f in files:
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out


def extract_diff_only(text: str) -> Optional[str]:
    idx = text.find("diff --git ")
    if idx < 0:
        return None
    return text[idx:].strip()


def run_cmd(cmd: List[str], cwd: Path, timeout: int = 300) -> Tuple[int, str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    return proc.returncode, proc.stdout


def git_porcelain2_is_clean(repo: Path) -> Tuple[bool, str]:
    code, out = run_cmd(["git", "status", "--porcelain=v2"], cwd=repo, timeout=60)
    if code != 0:
        return False, out.strip()
    return (out.strip() == ""), out.strip()


def git_apply_check(repo: Path, patch_path: Path) -> Tuple[bool, str]:
    code, out = run_cmd(["git", "apply", "--check", str(patch_path)], cwd=repo, timeout=120)
    return (code == 0), out.strip()


def write_audit_line(audit_path: Path, event: Dict[str, Any]) -> None:
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def send_tg(token: str, chat_id: int, text: str) -> Dict[str, Any]:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    return http_post_form(url, {"chat_id": chat_id, "text": text})


def tg_get_updates(token: str, offset: Optional[int], timeout_sec: int) -> Dict[str, Any]:
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    params: Dict[str, Any] = {"timeout": timeout_sec}
    if offset is not None:
        params["offset"] = offset
    return http_get(url, params, timeout=timeout_sec + 10)


def load_state(state_path: Path) -> Dict[str, Any]:
    if not state_path.exists():
        return {"update_offset": None, "last_task_by_chat": {}}
    try:
        st = json.loads(state_path.read_text(encoding="utf-8"))
        st.setdefault("update_offset", None)
        st.setdefault("last_task_by_chat", {})
        return st
    except Exception:
        return {"update_offset": None, "last_task_by_chat": {}}


def save_state(state_path: Path, st: Dict[str, Any]) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")


def build_task_json(task_id: str, chat_id: int, work_text: str, cfg: Cfg) -> Dict[str, Any]:
    return {
        "task_id": task_id,
        "source": "telegram",
        "command": cfg.work_cmd,
        "goal": work_text,
        "constraints": {
            "diff_only": True,
            "no_apply_no_commit_no_push": True,
            "no_remote_tools": True,
        },
        "scope": {
            "allowlist": cfg.allowlist,
            "denylist": cfg.denylist,
        },
        "gates": {
            "require_clean_porcelain2": cfg.require_clean_porcelain2,
            "require_git_apply_check": cfg.require_git_apply_check,
        },
        "meta": {
            "requested_by_chat_id": chat_id,
            "requested_at": _utc_iso(),
        },
    }


def run_claude_code_patch(work_text: str, cfg: Cfg, timeout_sec: int = 900) -> Tuple[bool, str, str]:
    prompt = "\n".join(cfg.prompt_template).format(WORK_TEXT=work_text)
    cmd = cfg.ollama_launch_cmd + ["--model", cfg.model_primary, "--", "-p", prompt]
    env = os.environ.copy()
    env["ANTHROPIC_BASE_URL"] = cfg.anthropic_base_url
    env.setdefault("ANTHROPIC_AUTH_TOKEN", os.environ.get("ANTHROPIC_AUTH_TOKEN", "LOCAL_ONLY"))
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cfg.repo_root),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_sec,
        )
        raw = proc.stdout
        diff = extract_diff_only(raw)
        if not diff:
            return False, raw, "NO_DIFF_FOUND"
        return True, diff, "OK"
    except subprocess.TimeoutExpired:
        return False, "", "TIMEOUT"


def validate_patch_text(patch_text: str, cfg: Cfg) -> Tuple[bool, str, List[str]]:
    if len(patch_text.encode("utf-8", errors="replace")) > cfg.max_patch_bytes:
        return False, "PATCH_TOO_LARGE", []
    if cfg.deny_binary_patches and "GIT binary patch" in patch_text:
        return False, "BINARY_PATCH_DENIED", []
    if cfg.deny_new_files and "new file mode" in patch_text:
        return False, "NEW_FILE_DENIED", []

    touched = parse_touched_files_from_patch(patch_text)
    if not touched:
        return False, "NO_TOUCHED_FILES", []

    for f in touched:
        if glob_match(f, cfg.denylist):
            return False, f"DENYLIST_VIOLATION:{f}", touched
        # allowlist는 glob 리스트. README.md 같은 단일 파일은 allowlist에 들어있으면 직접 비교도 허용
        if not glob_match(f, cfg.allowlist) and f not in cfg.allowlist:
            return False, f"ALLOWLIST_VIOLATION:{f}", touched
    return True, "OK", touched


def approve_task(task_id: str, chat_id: int, cfg: Cfg) -> Tuple[bool, str, Optional[Path]]:
    patch_path = cfg.patch_dir / f"{task_id}.patch"
    if not patch_path.exists():
        return False, "PATCH_NOT_FOUND", None

    # 안전을 위해 승인 시점에도 게이트 재확인
    clean, detail = git_porcelain2_is_clean(cfg.repo_root)
    if cfg.require_clean_porcelain2 and not clean:
        return False, "REPO_DIRTY", None

    ok_check, out_check = git_apply_check(cfg.repo_root, patch_path)
    if cfg.require_git_apply_check and not ok_check:
        return False, ("GIT_APPLY_CHECK_FAIL: " + (out_check[:1200] if out_check else "")), None

    approved = {
        "task_id": task_id,
        "approved_at": _utc_iso(),
        "approved_by_chat_id": chat_id,
        "patch_path": str(patch_path),
        "report_path": str(cfg.reports_dir / f"{task_id}.report.json"),
    }
    cfg.q_approved.mkdir(parents=True, exist_ok=True)
    approved_path = cfg.q_approved / f"{task_id}.approved.json"
    approved_path.write_text(json.dumps(approved, ensure_ascii=False, indent=2), encoding="utf-8")
    return True, "OK", approved_path


def main() -> int:
    load_env(ROOT / ".env")
    cfg_raw = load_json(ROOT / "config" / "WORK_AUTODEV_CONFIG.json")

    tg_token = os.environ.get(cfg_raw["telegram"]["bot_token_env"], "").strip()
    if not tg_token:
        print("[FATAL] TG_BOT_TOKEN is empty. Create .env from .env.example and set TG_BOT_TOKEN.", file=sys.stderr)
        return 2

    repo_root = Path(cfg_raw["project"]["repo_root"]).expanduser()
    if not repo_root.exists():
        print(f"[FATAL] repo_root not found: {repo_root}", file=sys.stderr)
        return 2

    q = cfg_raw["queue"]
    art = cfg_raw["artifacts"]
    cmds = cfg_raw["telegram"]["commands"]
    cfg = Cfg(
        repo_root=repo_root,
        tz=cfg_raw["project"]["timezone"],
        tg_token=tg_token,
        allowed_chat_ids=[int(x) for x in cfg_raw["telegram"]["allowed_chat_ids"]],
        work_cmd=cmds["work"],
        status_cmd=cmds["status"],
        stop_cmd=cmds["stop"],
        resume_cmd=cmds["resume"],
        help_cmd=cmds["help"],
        approve_cmd=cmds.get("approve", "/approve"),
        reject_cmd=cmds.get("reject", "/reject"),

        poll_timeout=int(cfg_raw["telegram"]["polling"]["timeout_sec"]),
        poll_interval=int(cfg_raw["telegram"]["polling"]["interval_sec"]),
        reply_rate_limit=int(cfg_raw["telegram"]["reply"]["rate_limit_sec"]),
        reply_max_chars=int(cfg_raw["telegram"]["reply"]["max_chars"]),

        engine=cfg_raw["automation"]["engine"],
        fallback_openclaw=bool(cfg_raw["automation"]["fallback_to_openclaw_queue"]),
        openclaw_wait_sec=int(cfg_raw["automation"]["openclaw_wait_sec"]),
        auto_stash_policy=cfg_raw["automation"]["auto_stash_policy"],

        tests_enabled=bool(cfg_raw["automation"]["tests"]["enabled"]),
        tests_cmd=cfg_raw["automation"]["tests"]["command"],
        tests_timeout=int(cfg_raw["automation"]["tests"]["timeout_sec"]),

        anthropic_base_url=cfg_raw["llm"]["ollama"]["anthropic_base_url"],
        model_primary=cfg_raw["llm"]["claude_code"]["model_primary"],
        model_fallbacks=cfg_raw["llm"]["claude_code"]["model_fallbacks"],
        ollama_launch_cmd=cfg_raw["llm"]["claude_code"]["ollama_launch_cmd"],
        prompt_template=cfg_raw["llm"]["claude_code"]["prompt_template"],

        allowlist=cfg_raw["scope"]["allowlist"],
        denylist=cfg_raw["scope"]["denylist"],

        q_root=repo_root / q["root"],
        q_inbox=repo_root / q["inbox"],
        q_work=repo_root / q["work"],
        q_blocked=repo_root / q["blocked"],
        q_audit=repo_root / q["audit"],
        q_approved=repo_root / q.get("approved", ".autodev_queue/approved"),
        killswitch=repo_root / q["killswitch"],

        patch_dir=repo_root / art["patch_dir"],
        reports_dir=repo_root / art["reports_dir"],
        runtime_dir=repo_root / art["runtime_dir"],

        max_patch_bytes=int(art["max_patch_bytes"]),
        max_report_bytes=int(art["max_report_bytes"]),

        require_clean_porcelain2=bool(cfg_raw["gates"]["require_clean_porcelain2"]),
        require_git_apply_check=bool(cfg_raw["gates"]["require_git_apply_check"]),
        deny_new_files=bool(cfg_raw["gates"]["deny_new_files"]),
        deny_binary_patches=bool(cfg_raw["gates"]["deny_binary_patches"]),

        tmpl_stop_repo_dirty=cfg_raw["report_templates"]["stop_repo_dirty"],
        tmpl_stop_killswitch=cfg_raw["report_templates"]["stop_killswitch"],
        tmpl_help=cfg_raw["report_templates"]["help"],
        tmpl_pass_patch_ready=cfg_raw["report_templates"]["pass_patch_ready"],
        tmpl_fail_patch_invalid=cfg_raw["report_templates"]["fail_patch_invalid"],
        tmpl_pass_approved=cfg_raw["report_templates"].get("pass_approved", "[APPROVED] {task_id}\n{approved_path}\n"),
        tmpl_fail_approve=cfg_raw["report_templates"].get("fail_approve", "[FAIL] Approve failed\n{reason}\n"),
    )

    ensure_dirs([cfg.q_inbox, cfg.q_work, cfg.q_blocked, cfg.q_audit, cfg.q_approved, cfg.patch_dir, cfg.runtime_dir])

    state_path = cfg.runtime_dir / "tg_state.json"
    st = load_state(state_path)
    offset = st.get("update_offset")
    last_task_by_chat = st.get("last_task_by_chat", {})

    last_reply_at = 0.0

    print("[OK] AutoDev Orchestrator started.")
    print(f"  repo_root: {cfg.repo_root}")
    print(f"  engine: {cfg.engine}")
    print(f"  allowed_chat_ids: {cfg.allowed_chat_ids}")

    while True:
        try:
            upd = tg_get_updates(cfg.tg_token, offset=offset, timeout_sec=cfg.poll_timeout)
        except Exception as e:
            print(f"[WARN] getUpdates error: {e}")
            time.sleep(2)
            continue

        if not upd.get("ok"):
            print(f"[WARN] getUpdates not ok: {upd}")
            time.sleep(2)
            continue

        results = upd.get("result", [])
        if not results:
            time.sleep(cfg.poll_interval)
            continue

        for item in results:
            offset = int(item["update_id"]) + 1
            st["update_offset"] = offset
            st["last_task_by_chat"] = last_task_by_chat
            save_state(state_path, st)

            msg = item.get("message") or item.get("edited_message")
            if not msg:
                continue
            chat = msg.get("chat", {})
            chat_id = int(chat.get("id", 0))
            text = (msg.get("text") or "").strip()
            if not text:
                continue

            if chat_id not in cfg.allowed_chat_ids:
                continue

            now = time.time()
            if now - last_reply_at < cfg.reply_rate_limit:
                continue

            # help
            if text.startswith(cfg.help_cmd):
                send_tg(cfg.tg_token, chat_id, cfg.tmpl_help[: cfg.reply_max_chars])
                last_reply_at = time.time()
                continue

            # stop/resume via TG
            if text.startswith(cfg.stop_cmd):
                cfg.killswitch.parent.mkdir(parents=True, exist_ok=True)
                cfg.killswitch.write_text("STOP\n", encoding="utf-8")
                send_tg(cfg.tg_token, chat_id, f"[OK] STOP enabled: {cfg.killswitch}")
                last_reply_at = time.time()
                continue

            if text.startswith(cfg.resume_cmd):
                if cfg.killswitch.exists():
                    try:
                        cfg.killswitch.unlink()
                    except Exception:
                        pass
                send_tg(cfg.tg_token, chat_id, "[OK] STOP cleared. Ready.")
                last_reply_at = time.time()
                continue

            # status
            if text.startswith(cfg.status_cmd):
                clean, detail = git_porcelain2_is_clean(cfg.repo_root)
                ks = cfg.killswitch.exists()
                msg_txt = f"[STATUS]\n- repo_clean: {clean}\n- killswitch: {ks}\n- engine: {cfg.engine}\n- last_task: {last_task_by_chat.get(str(chat_id))}\n"
                if not clean and detail:
                    msg_txt += f"- porcelain2: {detail[:800]}\n"
                send_tg(cfg.tg_token, chat_id, msg_txt[: cfg.reply_max_chars])
                last_reply_at = time.time()
                continue

            # approve
            if text.startswith(cfg.approve_cmd):
                if cfg.killswitch.exists():
                    out = cfg.tmpl_stop_killswitch.format(killswitch=str(cfg.killswitch))
                    send_tg(cfg.tg_token, chat_id, out[: cfg.reply_max_chars])
                    last_reply_at = time.time()
                    continue

                arg = text[len(cfg.approve_cmd):].strip()
                task_id = arg.split()[0] if arg else last_task_by_chat.get(str(chat_id))
                if not task_id:
                    send_tg(cfg.tg_token, chat_id, cfg.tmpl_fail_approve.format(task_id="(none)", reason="NO_TASK_ID")[: cfg.reply_max_chars])
                    last_reply_at = time.time()
                    continue

                ok_appr, reason, approved_path = approve_task(task_id, chat_id, cfg)
                if not ok_appr or not approved_path:
                    send_tg(cfg.tg_token, chat_id, cfg.tmpl_fail_approve.format(task_id=task_id, reason=reason)[: cfg.reply_max_chars])
                    write_audit_line(
                        cfg.q_audit / "events.ndjson",
                        {"ts": _utc_iso(), "actor": "orchestrator", "action": "APPROVE_FAIL", "task_id": task_id, "reason": reason},
                    )
                    last_reply_at = time.time()
                    continue

                send_tg(cfg.tg_token, chat_id, cfg.tmpl_pass_approved.format(task_id=task_id, approved_path=str(approved_path))[: cfg.reply_max_chars])
                write_audit_line(
                    cfg.q_audit / "events.ndjson",
                    {"ts": _utc_iso(), "actor": "orchestrator", "action": "APPROVED_FLAG_CREATED", "task_id": task_id, "approved_path": str(approved_path)},
                )
                last_reply_at = time.time()
                continue

            # reject (옵션): 승인 플래그 삭제(있으면) + 기록만
            if text.startswith(cfg.reject_cmd):
                arg = text[len(cfg.reject_cmd):].strip()
                task_id = arg.split()[0] if arg else last_task_by_chat.get(str(chat_id))
                if not task_id:
                    send_tg(cfg.tg_token, chat_id, "[FAIL] reject: NO_TASK_ID")
                    last_reply_at = time.time()
                    continue
                ap = cfg.q_approved / f"{task_id}.approved.json"
                if ap.exists():
                    try:
                        ap.unlink()
                    except Exception:
                        pass
                write_audit_line(cfg.q_audit / "events.ndjson", {"ts": _utc_iso(), "actor": "orchestrator", "action": "REJECTED", "task_id": task_id})
                send_tg(cfg.tg_token, chat_id, f"[OK] Rejected: {task_id}")
                last_reply_at = time.time()
                continue

            # work
            if not text.startswith(cfg.work_cmd):
                continue

            work_text = text[len(cfg.work_cmd):].strip()
            if not work_text:
                send_tg(cfg.tg_token, chat_id, "[FAIL] /work 뒤에 텍스트를 넣어주세요.")
                last_reply_at = time.time()
                continue

            if cfg.killswitch.exists():
                out = cfg.tmpl_stop_killswitch.format(killswitch=str(cfg.killswitch))
                send_tg(cfg.tg_token, chat_id, out[: cfg.reply_max_chars])
                last_reply_at = time.time()
                continue

            # Gate-0: repo clean
            clean, detail = git_porcelain2_is_clean(cfg.repo_root)
            if cfg.require_clean_porcelain2 and not clean:
                out = cfg.tmpl_stop_repo_dirty.format(repo_root=str(cfg.repo_root))
                send_tg(cfg.tg_token, chat_id, out[: cfg.reply_max_chars])
                write_audit_line(
                    cfg.q_audit / "events.ndjson",
                    {"ts": _utc_iso(), "actor": "orchestrator", "action": "STOP_REPO_DIRTY", "chat_id": chat_id, "detail": detail[:2000]},
                )
                last_reply_at = time.time()
                continue

            task_id = "T" + datetime.now().strftime("%Y%m%d-%H%M%S")
            task_json = build_task_json(task_id, chat_id, work_text, cfg)
            task_path = cfg.q_inbox / f"{task_id}__work.json"
            task_path.write_text(json.dumps(task_json, ensure_ascii=False, indent=2), encoding="utf-8")

            ok, diff_or_raw, code = run_claude_code_patch(work_text, cfg)
            if not ok:
                send_tg(cfg.tg_token, chat_id, cfg.tmpl_fail_patch_invalid.format(task_id=task_id, reason=code)[: cfg.reply_max_chars])
                write_audit_line(
                    cfg.q_audit / "events.ndjson",
                    {"ts": _utc_iso(), "actor": "orchestrator", "action": "CLAUDE_NO_DIFF", "task_id": task_id, "reason": code, "raw_hash": sha256_text(diff_or_raw) if diff_or_raw else None},
                )
                last_reply_at = time.time()
                continue

            patch_text = diff_or_raw
            valid, reason, touched = validate_patch_text(patch_text, cfg)
            if not valid:
                send_tg(cfg.tg_token, chat_id, cfg.tmpl_fail_patch_invalid.format(task_id=task_id, reason=reason)[: cfg.reply_max_chars])
                write_audit_line(cfg.q_audit / "events.ndjson", {"ts": _utc_iso(), "actor": "orchestrator", "action": "PATCH_INVALID", "task_id": task_id, "reason": reason, "touched": touched})
                last_reply_at = time.time()
                continue

            patch_path = cfg.patch_dir / f"{task_id}.patch"
            patch_path.write_text(patch_text, encoding="utf-8")

            if cfg.require_git_apply_check:
                ok_check, out_check = git_apply_check(cfg.repo_root, patch_path)
                if not ok_check:
                    reason2 = ("GIT_APPLY_CHECK_FAIL: " + out_check[:1200]) if out_check else "GIT_APPLY_CHECK_FAIL"
                    send_tg(cfg.tg_token, chat_id, cfg.tmpl_fail_patch_invalid.format(task_id=task_id, reason=reason2)[: cfg.reply_max_chars])
                    write_audit_line(cfg.q_audit / "events.ndjson", {"ts": _utc_iso(), "actor": "orchestrator", "action": "GATE_APPLY_CHECK_FAIL", "task_id": task_id, "detail": out_check[:3000]})
                    last_reply_at = time.time()
                    continue

            report = {
                "task_id": task_id,
                "ts": _utc_iso(),
                "source": "telegram",
                "chat_id": chat_id,
                "goal": work_text,
                "engine": "claude_code",
                "patch_path": str(patch_path),
                "touched": touched,
                "gates": {"porcelain2_clean": True, "git_apply_check": True},
                "hashes": {"patch_sha256": sha256_text(patch_text)},
            }
            report_path = cfg.reports_dir / f"{task_id}.report.json"
            report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

            write_audit_line(cfg.q_audit / "events.ndjson", {"ts": _utc_iso(), "actor": "orchestrator", "action": "PATCH_PROPOSED", "task_id": task_id, "patch_sha256": report["hashes"]["patch_sha256"], "touched": touched})

            # remember last task
            last_task_by_chat[str(chat_id)] = task_id
            st["last_task_by_chat"] = last_task_by_chat
            save_state(state_path, st)

            out = cfg.tmpl_pass_patch_ready.format(task_id=task_id, patch_path=str(patch_path))
            send_tg(cfg.tg_token, chat_id, out[: cfg.reply_max_chars])
            last_reply_at = time.time()

        time.sleep(cfg.poll_interval)


if __name__ == "__main__":
    raise SystemExit(main())
