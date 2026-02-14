#requires -Version 5.1
param(
  [ValidateSet("safe","long","quality","custom")]
  [string]$Preset = "safe"
)
$ErrorActionPreference = "Stop"

# =========================
# CONFIG (override via env)
# =========================
$VRAM_LIMIT_MIB = if ($env:VRAM_LIMIT_MIB) { [int]$env:VRAM_LIMIT_MIB } else { 7000 }
$GPU_INDEX      = if ($env:GPU_INDEX) { [int]$env:GPU_INDEX } else { 0 }

$MODEL_SAFE     = if ($env:MODEL_SAFE) { $env:MODEL_SAFE } else { "qcwind/qwen2.5-7B-instruct-Q4_K_M" }
$MODEL_QUALITY  = if ($env:MODEL_QUALITY) { $env:MODEL_QUALITY } else { "qcwind/qwen2.5-7B-instruct-Q5_K_M" }

$CTX_SAFE       = if ($env:CTX_SAFE) { [int]$env:CTX_SAFE } else { 4096 }
$CTX_LONG       = if ($env:CTX_LONG) { [int]$env:CTX_LONG } else { 8192 }

$THREADS_DEFAULT = if ($env:THREADS_DEFAULT) { [int]$env:THREADS_DEFAULT } else { 8 }

$Model   = if ($env:MODEL) { $env:MODEL } else { "" }
$Ctx     = if ($env:CTX) { [int]$env:CTX } else { 0 }
$Threads = if ($env:THREADS) { [int]$env:THREADS } else { $THREADS_DEFAULT }

function Get-OllamaModels {
  try {
    $out = & ollama list 2>$null
    if (-not $out) { return @() }
    return ($out | Select-Object -Skip 1 | ForEach-Object {
      ($_ -split "\s+")[0]
    }) | Where-Object { $_ -and $_.Trim().Length -gt 0 }
  } catch {
    return @()
  }
}

function Pick-Model([string]$want, [string]$fallbackSafe) {
  $models = Get-OllamaModels
  if ($models.Count -eq 0) { return "" }

  if ($want -and ($models -contains $want)) { return $want }

  if ($want) {
    $hit = $models | Where-Object { $_ -match [regex]::Escape($want) } | Select-Object -First 1
    if ($hit) { return $hit }
  }

  if ($models -contains $fallbackSafe) { return $fallbackSafe }
  return $models[0]
}

function Check-VRAM-OrStop([int]$limitMiB, [int]$gpuIndex) {
  $nvsmi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
  if (-not $nvsmi) {
    Write-Host "AMBER: nvidia-smi 미존재 → VRAM 체크 생략."
    return
  }

  try {
    $usedStr = & nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i $gpuIndex 2>$null | Select-Object -First 1
    if (-not $usedStr) {
      Write-Host "AMBER: nvidia-smi 값 읽기 실패 → VRAM 체크 생략."
      return
    }
    $used = [int]$usedStr.Trim()
    if ($used -gt $limitMiB) {
      Write-Host ("ZERO: VRAM 사용량 {0}.00MiB > 한도 {1}.00MiB → 실행 중단." -f $used, $limitMiB)
      exit 2
    }
  } catch {
    Write-Host "AMBER: VRAM 체크 중 예외 → 체크 생략."
  }
}

function Print-OllamaList {
  try {
    Write-Host "--- ollama list ---"
    & ollama list
    Write-Host ""
  } catch { }
}

# =========================
# APPLY PRESET
# =========================
switch ($Preset) {
  "safe" {
    if ($Ctx -le 0) { $Ctx = $CTX_SAFE }
    if (-not $Model) { $Model = $MODEL_SAFE }
  }
  "long" {
    if ($Ctx -le 0) { $Ctx = $CTX_LONG }
    if (-not $Model) { $Model = $MODEL_SAFE }
  }
  "quality" {
    if ($Ctx -le 0) { $Ctx = $CTX_SAFE }
    if (-not $Model) { $Model = $MODEL_QUALITY }
  }
  "custom" {
    if ($Ctx -le 0) { $Ctx = $CTX_SAFE }
  }
}

# =========================
# AUTO-DETECT MODEL
# =========================
$auto = Pick-Model $Model $MODEL_SAFE
if ($auto) { $Model = $auto }

if (-not $Model) {
  Write-Host "ZERO: 실행 가능한 모델을 찾지 못함(ollama list 비어있음 또는 ollama 미설치)."
  exit 3
}

# =========================
# ENV
# =========================
if (-not $env:OLLAMA_NUM_PARALLEL)    { $env:OLLAMA_NUM_PARALLEL    = "1" }
if (-not $env:OLLAMA_NUM_THREADS)     { $env:OLLAMA_NUM_THREADS     = "$Threads" }
if (-not $env:OLLAMA_FLASH_ATTENTION) { $env:OLLAMA_FLASH_ATTENTION = "1" }
if (-not $env:OMP_NUM_THREADS)        { $env:OMP_NUM_THREADS        = "6" }
if (-not $env:OLLAMA_NUM_CTX)         { $env:OLLAMA_NUM_CTX         = "$Ctx" }

# =========================
# PRE-RUN CHECKS
# =========================
Check-VRAM-OrStop $VRAM_LIMIT_MIB $GPU_INDEX

Write-Host "=== Ollama Launch ==="
Write-Host ("PRESET={0}" -f $Preset)
Write-Host ("MODEL={0}" -f $Model)
Write-Host ("CTX={0}" -f $Ctx)
Write-Host ("THREADS={0}" -f $env:OLLAMA_NUM_THREADS)
Write-Host ("PARALLEL={0}" -f $env:OLLAMA_NUM_PARALLEL)
Write-Host ("FLASH_ATTENTION={0}" -f $env:OLLAMA_FLASH_ATTENTION)
Write-Host ("VRAM_LIMIT_MIB={0}" -f $VRAM_LIMIT_MIB)
Write-Host ""

Print-OllamaList

& ollama run $Model
