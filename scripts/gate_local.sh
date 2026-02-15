#!/usr/bin/env bash
set -euo pipefail

PATCH="${1:-}"
TASK_JSON="${2:-}"
REPORT_JSON="${3:-}"

if [[ -z "${PATCH}" || ! -f "${PATCH}" ]]; then
  echo "[ERR] usage: ./scripts/gate_local.sh <path_to_patch> [task_json] [report_json]"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python "${SCRIPT_DIR}/gate_local.py" "${PATCH}" "${TASK_JSON}" "${REPORT_JSON}"
