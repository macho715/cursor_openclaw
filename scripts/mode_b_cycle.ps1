<#
.SYNOPSIS
Mode B one-cycle automation for task+patch gating and optional apply/commit/push.

.DESCRIPTION
This script enforces Mode B guardrails:
- local git status as SSOT
- git apply --check before apply
- allowlist/secret/test checks via scripts/gate_local.py

Typical interactive flow is two-phase:
1) Launch Claude and generate outputs.
2) Re-run with saved task/patch for gate and optional apply.

.EXAMPLE
powershell -ExecutionPolicy Bypass -File .\scripts\mode_b_cycle.ps1 -LaunchClaude -AutoStash

.EXAMPLE
powershell -ExecutionPolicy Bypass -File .\scripts\mode_b_cycle.ps1 -TaskJson .\tasks\T20260215-001.json -Patch .\patches\T20260215-001.patch

.EXAMPLE
powershell -ExecutionPolicy Bypass -File .\scripts\mode_b_cycle.ps1 -TaskJson .\tasks\T20260215-001.json -Patch .\patches\T20260215-001.patch -Apply -Commit -Push -CommitMessage "README: add (PROPOSED)"
#>
param(
    [string]$TaskJson = "",
    [string]$Patch = "",
    [string]$Model = "kwangsuklee/SEOKDONG-llama3.1_korean_Q5_K_M:latest",
    [switch]$AutoStash,
    [switch]$LaunchClaude,
    [switch]$Apply,
    [switch]$Commit,
    [switch]$Push,
    [string]$CommitMessage = "README: add (PROPOSED)"
)

$ErrorActionPreference = "Stop"

function Run-Step {
    param(
        [Parameter(Mandatory = $true)][string]$Message,
        [Parameter(Mandatory = $true)][scriptblock]$Action
    )
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
    & $Action
}

function Require-Command {
    param([Parameter(Mandatory = $true)][string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $Name"
    }
}

function Get-LatestFile {
    param(
        [Parameter(Mandatory = $true)][string]$Pattern,
        [Parameter(Mandatory = $true)][string]$Root
    )
    if (-not (Test-Path $Root)) {
        return ""
    }
    $file = Get-ChildItem -Path $Root -Recurse -File -Filter $Pattern |
        Sort-Object LastWriteTimeUtc -Descending |
        Select-Object -First 1
    if ($null -eq $file) {
        return ""
    }
    return $file.FullName
}

Require-Command "git"
Require-Command "python"

if (-not (Test-Path ".git")) {
    throw "Run this script at repository root."
}

New-Item -ItemType Directory -Force -Path ".\tasks" | Out-Null
New-Item -ItemType Directory -Force -Path ".\patches" | Out-Null

Run-Step -Message "Precheck: git worktree status" -Action {
    $status = git status --porcelain
    if (-not [string]::IsNullOrWhiteSpace($status)) {
        if ($AutoStash) {
            Write-Host "Worktree dirty -> auto stash enabled." -ForegroundColor Yellow
            git stash push -u -m "WIP before ModeB"
            $status2 = git status --porcelain
            if (-not [string]::IsNullOrWhiteSpace($status2)) {
                throw "Worktree is still dirty after stash."
            }
        } else {
            throw "Worktree is dirty. Use -AutoStash or clean it manually first."
        }
    }
    Write-Host "Worktree clean." -ForegroundColor Green
}

if ($LaunchClaude) {
    Run-Step -Message "Launch Claude on Ollama (interactive)" -Action {
        $prompt = @"
이 리포에서 README.md 첫 줄 끝에 ` (PROPOSED)`만 추가해.
반드시 README.md를 실제로 읽고, 존재하는 줄만 수정해(발명 금지).
출력은 아래 2블록만, 다른 텍스트/설명/예시 금지.

---BEGIN_TASK_JSON---
(task.json)
---END_TASK_JSON---

---BEGIN_PATCH---
(git apply 가능한 unified diff, README.md 1줄만 변경)
---END_PATCH---

마지막 줄은 정확히 GIT_STATUS_DELTA_EXPECTED=0
"@
        Write-Host "Paste this prompt in Claude after launch:" -ForegroundColor Yellow
        Write-Host $prompt
        try {
            Set-Clipboard -Value $prompt
            Write-Host "Prompt copied to clipboard." -ForegroundColor Green
        } catch {
            Write-Host "Clipboard copy skipped." -ForegroundColor Yellow
        }

        ollama launch claude --model $Model
    }
}

if ([string]::IsNullOrWhiteSpace($TaskJson)) {
    $TaskJson = Get-LatestFile -Pattern "T*.json" -Root ".\tasks"
}
if ([string]::IsNullOrWhiteSpace($Patch)) {
    $Patch = Get-LatestFile -Pattern "T*.patch" -Root ".\patches"
}

if ([string]::IsNullOrWhiteSpace($TaskJson) -or -not (Test-Path $TaskJson)) {
    throw "Task json not found. Provide -TaskJson .\tasks\TYYYYMMDD-001.json"
}
if ([string]::IsNullOrWhiteSpace($Patch) -or -not (Test-Path $Patch)) {
    throw "Patch file not found. Provide -Patch .\patches\TYYYYMMDD-001.patch"
}

$taskPath = (Resolve-Path $TaskJson).Path
$patchPath = (Resolve-Path $Patch).Path

Run-Step -Message "Gate 1: git apply --check" -Action {
    git apply --check $patchPath
    Write-Host "Gate 1 passed." -ForegroundColor Green
}

Run-Step -Message "Gate 2: gate_local.py allowlist/secret/test checks" -Action {
    python .\scripts\gate_local.py $patchPath $taskPath
    $gateJson = [System.IO.Path]::ChangeExtension($patchPath, ".gate.json")
    if (-not (Test-Path $gateJson)) {
        throw "Gate report missing: $gateJson"
    }
    $gate = Get-Content $gateJson -Raw | ConvertFrom-Json
    if ($gate.status -ne "PASS") {
        throw "Gate failed: $($gate.reason_code) $($gate.reason_detail)"
    }
    Write-Host "Gate 2 passed. ($($gate.reason_code))" -ForegroundColor Green
}

if (-not $Apply) {
    Write-Host ""
    Write-Host "[DONE] Gate PASS. Apply step skipped (use -Apply)." -ForegroundColor Green
    Write-Host "Task:  $taskPath"
    Write-Host "Patch: $patchPath"
    exit 0
}

Run-Step -Message "Apply patch (Cursor control-plane action)" -Action {
    git apply $patchPath
    git status --short
}

if ($Commit) {
    Run-Step -Message "Commit changes" -Action {
        git add -A
        git commit -m $CommitMessage
    }
}

if ($Push) {
    Run-Step -Message "Push to origin" -Action {
        git push
    }
}

Write-Host ""
Write-Host "[DONE] Mode B cycle completed." -ForegroundColor Green
Write-Host "Task:  $taskPath"
Write-Host "Patch: $patchPath"
