#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
Q="${ROOT}/.autodev_queue"

if [[ ! -d "${Q}/inbox" ]]; then
  echo "[ERR] queue not initialized. run: ./scripts/init_queue.sh"
  exit 1
fi

SRC="${1:-}"
if [[ -z "${SRC}" || ! -f "${SRC}" ]]; then
  echo "[ERR] usage: ./scripts/submit_task.sh <task.json>"
  exit 1
fi

TS="$(date -u +%Y%m%dT%H%M%SZ)"
BASENAME="$(basename "${SRC}")"
DST="${Q}/inbox/${TS}__${BASENAME}"

cp "${SRC}" "${DST}"
echo "[OK] submitted: ${DST}"
