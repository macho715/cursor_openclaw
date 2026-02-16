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

# Gate-0: repo clean (권장)
$por = git status --porcelain=v2
if ($por) {
  Write-Host "[STOP] Repo dirty. Clean first. porcelain2:"
  Write-Host $por
  exit 3
}

# PR branch (approve 단계에서 생성됐을 가능성)
$branch = $ap.pr_branch
if (-not $branch) { $branch = "autodev/$TaskId" }
$baseSha = $ap.pr_base_sha

# checkout / create branch (Cursor에서만 수행)
Write-Host "[INFO] Target PR branch:" $branch

git show-ref --verify --quiet ("refs/heads/" + $branch)
if ($LASTEXITCODE -eq 0) {
  Write-Host "[OK] Branch exists. checkout:" $branch
  git checkout $branch
} else {
  if ($baseSha) {
    Write-Host "[OK] Creating branch from base sha:" $baseSha
    git checkout -b $branch $baseSha
  } else {
    Write-Host "[OK] Creating branch from current HEAD"
    git checkout -b $branch
  }
}

# Gate-0b: checkout 후 clean 확인(여전히 clean이어야 함)
$por2 = git status --porcelain=v2
if ($por2) {
  Write-Host "[STOP] Repo dirty after checkout. porcelain2:"
  Write-Host $por2
  exit 3
}

# Gate-1: apply --check
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
Write-Host "  git commit -am ""autodev: $TaskId"""
Write-Host "  git push -u origin ""$branch"""
Write-Host "  (GitHub에서 PR 생성: base=main, compare=$branch)"
