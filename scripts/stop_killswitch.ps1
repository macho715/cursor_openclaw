Param(
  [string]$RepoRoot = ""
)
$ErrorActionPreference = "Stop"
if ($RepoRoot -eq "") { $RepoRoot = (Get-Location).Path }
Set-Location $RepoRoot

$stopFile = ".\.autodev_queue\STOP"
Set-Content -Path $stopFile -Value "STOP" -Encoding utf8
Write-Host "[OK] STOP enabled:" $stopFile
