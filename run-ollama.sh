#!/usr/bin/env bash
set -euo pipefail

VRAM_LIMIT_MIB="${VRAM_LIMIT_MIB:-7000}"
GPU_INDEX="${GPU_INDEX:-0}"
MODEL_SAFE="${MODEL_SAFE:-qcwind/qwen2.5-7B-instruct-Q4_K_M}"
MODEL_QUALITY="${MODEL_QUALITY:-qcwind/qwen2.5-7B-instruct-Q5_K_M}"
CTX_SAFE="${CTX_SAFE:-4096}"
CTX_LONG="${CTX_LONG:-8192}"
THREADS_DEFAULT="${THREADS_DEFAULT:-8}"

PRESET="${1:-safe}"
MODEL="${MODEL:-}"
CTX="${CTX:-}"
THREADS="${THREADS:-$THREADS_DEFAULT}"

has_cmd() { command -v "$1" >/dev/null 2>&1; }

pick_model_from_ollama_list() {
  local want="${1:-}"
  if ! has_cmd ollama; then echo ""; return 0; fi
  local models
  models="$(ollama list 2>/dev/null | awk 'NR>1{print $1}' || true)"
  if [[ -z "$models" ]]; then echo ""; return 0; fi
  if [[ -n "$want" ]]; then
    if echo "$models" | grep -Fxq "$want"; then echo "$want"; return 0; fi
    local hit
    hit="$(echo "$models" | grep -i "$want" | head -n 1 || true)"
    if [[ -n "$hit" ]]; then echo "$hit"; return 0; fi
  fi
  if echo "$models" | grep -Fxq "$MODEL_SAFE"; then echo "$MODEL_SAFE"; return 0; fi
  echo "$models" | head -n 1
}

check_vram_or_stop() {
  if ! has_cmd nvidia-smi; then echo "AMBER: nvidia-smi missing, skip VRAM check"; return 0; fi
  local used
  used="$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i "$GPU_INDEX" 2>/dev/null | head -n 1 || true)"
  if [[ -z "$used" ]]; then echo "AMBER: nvidia-smi read failed"; return 0; fi
  if [[ "$used" -gt "$VRAM_LIMIT_MIB" ]]; then
    echo "ZERO: VRAM ${used}MiB > limit ${VRAM_LIMIT_MIB}MiB, abort"
    exit 2
  fi
}

case "$PRESET" in
  safe) CTX="${CTX:-$CTX_SAFE}"; MODEL="${MODEL:-$MODEL_SAFE}" ;;
  long) CTX="${CTX:-$CTX_LONG}"; MODEL="${MODEL:-$MODEL_SAFE}" ;;
  quality) CTX="${CTX:-$CTX_SAFE}"; MODEL="${MODEL:-$MODEL_QUALITY}" ;;
  custom) CTX="${CTX:-$CTX_SAFE}" ;;
  *) echo "Usage: $0 [safe|long|quality|custom]"; exit 1 ;;
esac

AUTO_MODEL="$(pick_model_from_ollama_list "$MODEL")"
[[ -n "$AUTO_MODEL" ]] && MODEL="$AUTO_MODEL"

if [[ -z "$MODEL" ]]; then
  echo "ZERO: No model found (ollama list empty or ollama not installed)"
  exit 3
fi

export OLLAMA_NUM_PARALLEL="${OLLAMA_NUM_PARALLEL:-1}"
export OLLAMA_NUM_THREADS="${OLLAMA_NUM_THREADS:-$THREADS}"
export OLLAMA_FLASH_ATTENTION="${OLLAMA_FLASH_ATTENTION:-1}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-6}"

check_vram_or_stop

echo "=== Ollama Launch ==="
echo "PRESET=$PRESET MODEL=$MODEL CTX=$CTX VRAM_LIMIT_MIB=$VRAM_LIMIT_MIB"
has_cmd ollama && ollama list
exec ollama run "$MODEL" --context "$CTX"
