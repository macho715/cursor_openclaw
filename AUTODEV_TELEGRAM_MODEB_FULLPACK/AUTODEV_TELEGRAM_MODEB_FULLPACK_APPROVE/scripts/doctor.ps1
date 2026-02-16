Param(
  [string]$RepoRoot = ""
)
$ErrorActionPreference = "Continue"
if ($RepoRoot -eq "") { $RepoRoot = (Get-Location).Path }
Set-Location $RepoRoot

Write-Host "=== AutoDev Doctor ==="
Write-Host "[1] repo root:" (Get-Location).Path

Write-Host "[2] git:"
git --version

Write-Host "[3] ollama:"
ollama --version

Write-Host "[4] claude:"
claude --version

Write-Host "[5] git status porcelain2:"
git status --porcelain=v2

Write-Host "[6] env:"
if (Test-Path .\.env) { Write-Host ".env: OK" } else { Write-Host ".env: MISSING" }

Write-Host "[7] queue dirs:"
Get-ChildItem .\.autodev_queue -ErrorAction SilentlyContinue | Select-Object Name

Write-Host "[8] approved flags:" 
Get-ChildItem .\.autodev_queue\approved -ErrorAction SilentlyContinue | Select-Object Name

Write-Host "=== END ==="
