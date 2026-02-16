Param(
  [string]$RepoRoot = ""
)
$ErrorActionPreference = "Stop"
if ($RepoRoot -eq "") { $RepoRoot = (Get-Location).Path }
Set-Location $RepoRoot

$stopFile = ".\.autodev_queue\STOP"
if (Test-Path $stopFile) {
  Remove-Item $stopFile -Force
}
Write-Host "[OK] STOP cleared"
