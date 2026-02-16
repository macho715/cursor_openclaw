Param(
  [string]$RepoRoot = ""
)

$ErrorActionPreference = "Stop"

Write-Host "[AutoDev] Install 시작"

if ($RepoRoot -eq "") {
  $RepoRoot = (Get-Location).Path
}

Set-Location $RepoRoot

if (-not (Test-Path ".\config\WORK_AUTODEV_CONFIG.json")) {
  Write-Host "[FATAL] config\WORK_AUTODEV_CONFIG.json 없음. 팩을 repo 루트에 풀었는지 확인."
  exit 2
}

# 1) .env 생성(없으면)
if (-not (Test-Path ".\.env")) {
  Copy-Item ".\.env.example" ".\.env"
  Write-Host "[OK] .env 생성됨"
} else {
  Write-Host "[OK] .env 이미 존재"
}

# 2) 사용자 입력(선택): TG token
$envText = Get-Content ".\.env" -Raw
if ($envText -match "TG_BOT_TOKEN=PASTE_") {
  $tok = Read-Host "TG_BOT_TOKEN 입력(BotFather). 입력 후 Enter"
  if ($tok) {
    $envText = $envText -replace "TG_BOT_TOKEN=PASTE_YOUR_TELEGRAM_BOT_TOKEN_HERE", ("TG_BOT_TOKEN=" + $tok)
    Set-Content -Path ".\.env" -Value $envText -Encoding utf8
    Write-Host "[OK] .env에 TG_BOT_TOKEN 반영"
  } else {
    Write-Host "[WARN] TG_BOT_TOKEN 미입력. 나중에 .env 수정 필요"
  }
}

# 3) config 자동 반영: repo_root=현재 폴더 (기본)
$cfgPath = ".\config\WORK_AUTODEV_CONFIG.json"
$cfg = Get-Content $cfgPath -Raw | ConvertFrom-Json
$cfg.project.repo_root = $RepoRoot

# 4) (선택) chat_id 업데이트
$curChat = $cfg.telegram.allowed_chat_ids[0]
$chat = Read-Host "allowed chat_id (기본: $curChat) 그대로면 Enter"
if ($chat) {
  $cfg.telegram.allowed_chat_ids = @([int]$chat)
  Write-Host "[OK] allowed_chat_ids 업데이트:" $chat
}

# 5) JSON 저장
($cfg | ConvertTo-Json -Depth 99) | Set-Content $cfgPath -Encoding utf8
Write-Host "[OK] config 업데이트: repo_root=$RepoRoot"

# 6) queue/runtime/patches 디렉토리 생성
$dirs = @(
  ".\.autodev_queue\inbox",
  ".\.autodev_queue\work",
  ".\.autodev_queue\blocked",
  ".\.autodev_queue\audit",
  ".\.autodev_queue\approved",
  ".\.autodev_runtime",
  ".\patches",
  ".\logs"
)
foreach ($d in $dirs) {
  New-Item -ItemType Directory -Force $d | Out-Null
}

# 7) 기본 체크(ollama/git/python/claude)
Write-Host "[CHECK] git / ollama / python / claude"
git --version | Out-Null
ollama --version | Out-Null
python --version | Out-Null
claude --version | Out-Null

Write-Host "[OK] Install 완료"
Write-Host "다음: scripts\run_orchestrator.ps1 실행 (또는 scripts\install_task_onlogon.ps1)"
