from __future__ import annotations

import subprocess
from pathlib import Path


def run_git(args: list[str], repo_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


def is_repo_clean(repo_root: Path) -> bool:
    result = run_git(["status", "--porcelain"], repo_root)
    return result.returncode == 0 and result.stdout.strip() == ""


def apply_check(repo_root: Path, patch_path: Path) -> tuple[bool, str]:
    result = run_git(["apply", "--check", str(patch_path)], repo_root)
    if result.returncode == 0:
        return True, ""
    detail = (result.stderr or result.stdout).strip()
    return False, detail
