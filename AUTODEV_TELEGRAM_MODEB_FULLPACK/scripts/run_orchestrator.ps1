Param(
  [string]$RepoRoot = ""
)
$ErrorActionPreference = "Stop"
if ($RepoRoot -eq "") { $RepoRoot = (Get-Location).Path }
Set-Location $RepoRoot

# UTF-8 콘솔
chcp 65001 | Out-Null

Write-Host "[AutoDev] Orchestrator 실행"
python .\orchestrator\tg_orchestrator.py
