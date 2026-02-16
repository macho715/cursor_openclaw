Param(
  [string]$RepoRoot = ""
)
$ErrorActionPreference = "Stop"
if ($RepoRoot -eq "") { $RepoRoot = (Get-Location).Path }
Set-Location $RepoRoot

powershell -ExecutionPolicy Bypass -File .\scripts\install_windows.ps1 -RepoRoot $RepoRoot
powershell -ExecutionPolicy Bypass -File .\scripts\run_orchestrator.ps1 -RepoRoot $RepoRoot
