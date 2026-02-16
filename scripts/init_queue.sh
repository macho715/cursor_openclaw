#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
Q="${ROOT}/.autodev_queue"

mkdir -p "${Q}"/{inbox,claimed,work,pr,done,blocked,audit}

touch "${Q}/audit/events.ndjson"

cat > "${Q}/README_QUEUE.md" <<'EOF'
# .autodev_queue
- inbox: 새 task.json 투입
- claimed: 워커가 claim한 task
- work: patch/report 산출물
- pr: Cursor가 PR 후보로 정리(선택)
- done: 완료
- blocked: STOP/검증실패/정보부족
- audit: events.ndjson (append-only)
- STOP: 존재하면 워커 즉시 중단
EOF

touch "${Q}/.keep"

echo "[OK] Queue initialized at: ${Q}"
echo "      Kill-switch: ${Q}/STOP"
