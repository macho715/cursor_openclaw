
from __future__ import annotations

import argparse
from pathlib import Path

# STOP 제외: 킬스위치 활성화 시에만 생성
QUEUE_DIRS = ["inbox", "claimed", "work", "pr", "done", "blocked", "audit"]

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".autodev_queue")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    root = Path(args.root)
    dry_run = args.dry_run or not args.apply

    actions = [f"mkdir -p {root / d}" for d in QUEUE_DIRS]
    if dry_run:
        print("[DRY_RUN] Would create:")
        for a in actions:
            print(" -", a)
        print("\nTo apply: python tools/init_autodev_queue.py --apply")
        return 0

    for d in QUEUE_DIRS:
        p = root / d
        p.mkdir(parents=True, exist_ok=True)
        (p / ".gitkeep").write_text("", encoding="utf-8")
    print("[APPLY] Created", root)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
