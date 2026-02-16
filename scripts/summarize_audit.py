import json
from pathlib import Path
from collections import Counter

AUDIT = Path(".autodev_queue/audit/events.ndjson")


def main():
    if not AUDIT.exists():
        print("[ERR] audit file not found:", AUDIT)
        return

    actions = Counter()
    actors = Counter()
    levels = Counter()

    for line in AUDIT.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        ev = json.loads(line)
        actions[ev.get("action")] += 1
        actors[ev.get("actor")] += 1
        levels[ev.get("level")] += 1

    print("== actions ==")
    for k, v in actions.most_common():
        print(f"{k}: {v}")

    print("\n== actors ==")
    for k, v in actors.most_common():
        print(f"{k}: {v}")

    print("\n== levels ==")
    for k, v in levels.most_common():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
