# Minimal preflight - only writes log and exits. Use to verify logging works before full diagnose.
$p1 = "c:\Users\jichu\Downloads\cursor_full_setting_optionA\.cursor\debug.log"
$p2 = Join-Path $env:TEMP "stack_diag_debug.log"
$dir = Split-Path $p1 -Parent
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
$e = @{ id = "preflight_ok"; timestamp = [long](((Get-Date) - (Get-Date "1970-01-01")).TotalMilliseconds); message = "PREFLIGHT_ONLY"; hypothesisId = "H0" } | ConvertTo-Json -Compress
try { [System.IO.File]::AppendAllText($p2, $e + "`n") } catch {}
try { [System.IO.File]::AppendAllText($p1, $e + "`n") } catch {}
Write-Host "Preflight done. Check: $p1 or $p2"
