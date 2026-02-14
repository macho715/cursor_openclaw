# Stack install diagnostic - logs each phase
$ErrorActionPreference = "Continue"
$LogPath = "c:\Users\jichu\Downloads\cursor_full_setting_optionA\.cursor\debug.log"
$LogPathTemp = Join-Path $env:TEMP "stack_diag_debug.log"
$LogDir = Split-Path $LogPath -Parent
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }

function Write-DebugLog {
  param([string]$Phase, [string]$Event, [string]$HypothesisId, [hashtable]$Data = @{})
  try {
    $ts = [long](((Get-Date) - (Get-Date "1970-01-01")).TotalMilliseconds)
    $dataObj = @{ phase = $Phase; event = $Event }
    foreach ($k in $Data.Keys) { $dataObj[$k] = $Data[$k] }
    $entry = @{ id = "diag_$ts"; timestamp = $ts; location = "diagnose-install.ps1"; message = "$Phase - $Event"; hypothesisId = $HypothesisId; data = $dataObj } | ConvertTo-Json -Compress -Depth 4
    foreach ($p in @($LogPath, $LogPathTemp)) { try { [System.IO.File]::AppendAllText($p, $entry + "`n") } catch {} }
  } catch {}
}

# #region agent log - first write (TEMP first - always writable)
$ts0 = [long](((Get-Date) - (Get-Date "1970-01-01")).TotalMilliseconds)
$e0 = @{ id = "diag_script_start"; timestamp = $ts0; location = "diagnose-install.ps1:1"; message = "SCRIPT_START"; hypothesisId = "H0"; data = @{ phase = "INIT"; event = "script_loaded" } } | ConvertTo-Json -Compress
try { [System.IO.File]::AppendAllText($LogPathTemp, $e0 + "`n") } catch {}
try { [System.IO.File]::AppendAllText($LogPath, $e0 + "`n") } catch {}
# #endregion

$stackDir = "c:\Users\jichu\Downloads\cursor_full_setting_optionA\stack"
Set-Location $stackDir

# Pre-check
$vram = $null
try { $vram = (nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits 2>$null) } catch {}
$mem = $null
try { $mem = (Get-CimInstance Win32_OperatingSystem 2>$null | Select-Object -ExpandProperty FreePhysicalMemory) / 1MB } catch {}

Write-DebugLog -Phase "PRE" -Event "start" -HypothesisId "H0" -Data @{ vram_raw = "$vram"; free_ram_mb = if ($mem) { [math]::Round($mem, 2) } else { "N/A" } }

# Phase 1: Ollama pull + start
Write-DebugLog -Phase "PHASE1" -Event "before_ollama_pull" -HypothesisId "H1"
docker compose pull ollama 2>&1 | Out-Null
Write-DebugLog -Phase "PHASE1" -Event "after_ollama_pull" -HypothesisId "H1"

Write-DebugLog -Phase "PHASE1" -Event "before_ollama_up" -HypothesisId "H2"
docker compose up -d ollama 2>&1 | Out-Null
Write-DebugLog -Phase "PHASE1" -Event "after_ollama_up" -HypothesisId "H2"

Start-Sleep -Seconds 15
Write-DebugLog -Phase "PHASE1" -Event "after_ollama_sleep" -HypothesisId "H3"

# Phase 2: openclaw
Write-DebugLog -Phase "PHASE2" -Event "before_openclaw_build" -HypothesisId "H4"
docker compose up -d openclaw 2>&1 | Out-Null
Write-DebugLog -Phase "PHASE2" -Event "after_openclaw_up" -HypothesisId "H4"

Start-Sleep -Seconds 10

# Phase 3: prometheus, grafana
Write-DebugLog -Phase "PHASE3" -Event "before_monitoring" -HypothesisId "H5"
docker compose up -d prometheus grafana 2>&1 | Out-Null
Write-DebugLog -Phase "PHASE3" -Event "after_monitoring" -HypothesisId "H5"

Write-DebugLog -Phase "DONE" -Event "complete" -HypothesisId "H0"
