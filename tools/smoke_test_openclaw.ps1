# OpenClaw Gateway 호스트 스모크 테스트 (Windows)
# 사용: .\tools\smoke_test_openclaw.ps1
# 토큰(선택): $env:OPENCLAW_TOKEN 설정 또는 -Token "..." 인자 (로그에 기록되지 않음)
param([string]$Token = $env:OPENCLAW_TOKEN)

$ErrorActionPreference = "Continue"
$PASS = 0
$FAIL = 0
$SKIP = 0

function Write-Result($Step, $Ok, $Msg) {
    $status = if ($Ok) { "PASS"; $script:PASS++ } else { "FAIL"; $script:FAIL++ }
    Write-Host "[$status] $Step : $Msg" -ForegroundColor $(if ($Ok) { "Green" } else { "Red" })
}

function Write-Skip($Step, $Msg) {
    Write-Host "[SKIP] $Step : $Msg" -ForegroundColor Yellow
    $script:SKIP++
}

# 1-1) 포트 리스닝 확인
Write-Host "`n--- 1-1 Port 18789 (Gateway) ---"
try {
    $t18789 = Test-NetConnection 127.0.0.1 -Port 18789 -WarningAction SilentlyContinue
    Write-Result "1-1a" $t18789.TcpTestSucceeded "Gateway 18789"
} catch { Write-Result "1-1a" $false $_.Exception.Message }

Write-Host "`n--- 1-1 Port 11434 (Ollama) ---"
try {
    $t11434 = Test-NetConnection 127.0.0.1 -Port 11434 -WarningAction SilentlyContinue
    Write-Result "1-1b" $t11434.TcpTestSucceeded "Ollama 11434"
} catch { Write-Result "1-1b" $false $_.Exception.Message }

# 1-2) Ollama /v1/models
Write-Host "`n--- 1-2 Ollama /v1/models ---"
try {
    $r = curl.exe -sS http://127.0.0.1:11434/v1/models 2>&1
    $hasData = $r -match '"data"|"models"'
    Write-Result "1-2" $hasData "Ollama JSON response"
} catch { Write-Result "1-2" $false $_.Exception.Message }

# 1-3) Gateway /?token= (토큰 미제공 시 SKIP)
Write-Host "`n--- 1-3 Gateway token check ---"
if (-not $Token) {
    Write-Skip "1-3" "Token not provided (set OPENCLAW_TOKEN or -Token)"
} else {
    try {
        $h = curl.exe -sS -I "http://127.0.0.1:18789/?token=$Token" 2>&1
        $ok = $h -match "HTTP/1\.1 (200|302)"
        Write-Result "1-3" $ok "Gateway HTTP response"
    } catch { Write-Result "1-3" $false $_.Exception.Message }
}

# 1-4) Docker sandbox Up
Write-Host "`n--- 1-4 Docker sandbox ---"
$containerName = $null
try {
    $out = docker ps --filter "name=openclaw-sbx" --format "{{.Names}}\t{{.Status}}" 2>&1 | Out-String
    $upCount = ([regex]::Matches($out, "Up")).Count
    if ($out -match "error|Cannot") { $upCount = 0 }
    Write-Result "1-4" ($upCount -ge 1) "openclaw-sbx Up count=$upCount"
    if ($upCount -ge 1 -and $out -match "([^\s`t]+)\t") { $containerName = $Matches[1] }
} catch { Write-Result "1-4" $false $_.Exception.Message }

# 1-5) Mount 개수 (1-4에서 컨테이너 이름 사용)
Write-Host "`n--- 1-5 Sandbox Mount count ---"
if ($containerName) {
    try {
        $mounts = docker inspect $containerName --format "{{len .Mounts}}" 2>&1
        $n = [int]$mounts
        Write-Result "1-5" ($true) "Mounts=$n (0 권장)"
    } catch { Write-Result "1-5" $false $_.Exception.Message }
} else {
    Write-Skip "1-5" "No openclaw-sbx container found"
}

# 1-6) netstat LISTENING
Write-Host "`n--- 1-6 netstat LISTENING ---"
try {
    $n18789 = netstat -ano 2>$null | findstr ":18789"
    $n11434 = netstat -ano 2>$null | findstr ":11434"
    $ok18789 = $n18789 -match "LISTENING"
    $ok11434 = $n11434 -match "LISTENING"
    Write-Result "1-6a" $ok18789 "18789 LISTENING"
    Write-Result "1-6b" $ok11434 "11434 LISTENING"
} catch { Write-Result "1-6" $false $_.Exception.Message }

# 요약
Write-Host "`n--- Summary ---"
Write-Host "PASS: $PASS | FAIL: $FAIL | SKIP: $SKIP"
if ($FAIL -gt 0) { exit 1 } else { exit 0 }
