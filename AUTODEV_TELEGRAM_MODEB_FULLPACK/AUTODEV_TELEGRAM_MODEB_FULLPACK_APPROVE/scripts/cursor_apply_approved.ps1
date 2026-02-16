Param(
  [string]$RepoRoot = "",
  [string]$TaskId = ""
)
$ErrorActionPreference = "Stop"
if ($RepoRoot -eq "") { $RepoRoot = (Get-Location).Path }
Set-Location $RepoRoot

$approvedDir = ".\.autodev_queue\approved"
if (-not (Test-Path $approvedDir)) {
  Write-Host "[FATAL] approved dir not found:" $approvedDir
  exit 2
}

# TaskId 없으면 최신 승인 파일 선택
if ($TaskId -eq "") {
  $latest = Get-ChildItem $approvedDir -Filter "*.approved.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if (-not $latest) {
    Write-Host "[FATAL] No approved tasks."
    exit 2
  }
  $TaskId = [System.IO.Path]::GetFileNameWithoutExtension($latest.Name).Replace(".approved","")
}

$apPath = Join-Path $approvedDir ($TaskId + ".approved.json")
if (-not (Test-Path $apPath)) {
  Write-Host "[FATAL] Approved file missing:" $apPath
  exit 2
}

$ap = Get-Content $apPath -Raw | ConvertFrom-Json
$patchPath = $ap.patch_path
if (-not (Test-Path $patchPath)) {
  Write-Host "[FATAL] Patch missing:" $patchPath
  exit 2
}

# Gate: repo clean (권장)
$por = git status --porcelain=v2
if ($por) {
  Write-Host "[STOP] Repo dirty. Clean first. porcelain2:"
  Write-Host $por
  exit 3
}

Write-Host "[CHECK] git apply --check" $patchPath
git apply --check $patchPath
if ($LASTEXITCODE -ne 0) {
  Write-Host "[FAIL] apply --check failed"
  exit 4
}

Write-Host "[OK] Applying patch (Cursor/manual trigger)"
git apply $patchPath

Write-Host "[OK] Applied. Next (manual):"
Write-Host "  git status --porcelain"
Write-Host "  git commit -am ""<message>"""
Write-Host "  git push"
