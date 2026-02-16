Param(
  [string]$RepoRoot = "",
  [string]$TaskName = "AutoDev-ModeB-Orchestrator"
)
$ErrorActionPreference = "Stop"
if ($RepoRoot -eq "") { $RepoRoot = (Get-Location).Path }
Set-Location $RepoRoot

$script = Join-Path $RepoRoot "scripts\run_orchestrator.ps1"
$cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$script`" -RepoRoot `"$RepoRoot`""

Write-Host "[INFO] Creating scheduled task:" $TaskName
schtasks /Create /F /SC ONLOGON /TN $TaskName /TR $cmd
Write-Host "[OK] Done. (ONLOGON)"
