# Mode B 운영 Runbook

**조건부 Go** — Claude 산출(task.json + diff) 허용, 단 **SSOT=로컬 Git** + `git apply --check` 통과 전까지 **무조건 미적용**.

---

## 1. 역할 정의(4툴)

| 툴 | 역할 |
|----|------|
| **Ollama** | 로컬 LLM 엔진(모델 실행기) |
| **Claude Code** | 사람-대화 + **티켓(task.json) + diff 제안** |
| **OpenClaw** | 워커 — diff/patch 제안(선택 경로) |
| **Cursor** | 컨트롤 플레인 — **apply/test/commit/PR/merge 전담** |

---

## 2. Mode B 운영 규칙(SSOT 고정 8)

1. **Claude 산출은 2개만 인정**: `task.json` + `unified diff`
2. Claude 출력에 **설명/예시/가짜 상태(git status 예시)** 섞이면 **즉시 폐기**
3. diff는 **반드시 로컬에서 `git apply --check`** 통과해야만 "유효"
4. check 통과 전까지는 **`git apply` 금지**
5. touched files는 **allowlist** 밖이면 **즉시 FAIL**
6. Repo가 dirty면 먼저 **stash/reset로 기준점 확보** 후 진행
7. Claude는 "파일 읽고 존재하는 줄만 수정" 강제(발명 금지)
8. 최종 적용/커밋은 **Cursor(Control-Plane)** 에서만 수행(권한 분리)

---

## 3. 1사이클 Runbook(10분, 복붙)

### Step 0) 시작 상태 확인

```powershell
cd C:\Users\jichu\Downloads\cursor_full_setting_optionA\cursor_openclaw
git status --porcelain
```

* 빈 출력 아니면:

```powershell
git stash push -u -m "WIP before ModeB"
git status --porcelain
```

### Step 1) Claude Code 실행(로컬 Ollama)

```powershell
ollama launch claude --model kwangsuklee/SEOKDONG-llama3.1_korean_Q5_K_M:latest
```

### Step 2) Claude 프롬프트(티켓+diff 동시 산출, 출력 포맷 강제)

아래를 그대로 붙여:

> "이 리포에서 README.md 첫 줄 끝에 ` (PROPOSED)`만 추가해.
> **반드시 README.md를 실제로 읽고**, 존재하는 줄만 수정해(발명 금지).
> 출력은 아래 2블록만, 다른 텍스트/설명/예시 금지.
>
> ---BEGIN_TASK_JSON---
> (task.json)
> ---END_TASK_JSON---
>
> ---BEGIN_PATCH---
> (git apply 가능한 unified diff, README.md 1줄만 변경)
> ---END_PATCH---
>
> 마지막 줄은 정확히 `GIT_STATUS_DELTA_EXPECTED=0`"

### Step 3) 산출물 저장(로컬)

Claude 출력에서 두 블록만 각각 파일로 저장:

* `tasks/TYYYYMMDD-001.json`
* `patches/TYYYYMMDD-001.patch`

```powershell
mkdir tasks, patches -Force | Out-Null
```

### Step 4) Gate 1: patch 유효성(필수)

```powershell
git apply --check .\patches\TYYYYMMDD-001.patch
echo $LASTEXITCODE
```

* **PASS:** `0`
* **FAIL:** 즉시 폐기(다시 생성 요청)

### Step 5) Gate 2: allowlist(필수)

patch가 허용 경로만 건드리는지 확인:

```powershell
Select-String -Path .\patches\TYYYYMMDD-001.patch -Pattern "^\+\+\+ b/" | ForEach-Object { $_.Line }
```

* `+++ b/README.md`만 있어야 PASS (작업별 허용 목록 참조)

### Step 6) (Cursor에서만) 적용/커밋

```powershell
git apply .\patches\TYYYYMMDD-001.patch
git status --porcelain
git commit -am "README: add (PROPOSED)"
git push
```

### 자동화 스크립트(권장)

`scripts/mode_b_cycle.ps1`로 Gate/Apply/Commit/Push를 일괄 처리할 수 있다.

```powershell
# 완전 인터랙티브 1단계: Claude 실행 + 프롬프트 자동 표시/클립보드 복사
powershell -ExecutionPolicy Bypass -File .\scripts\mode_b_cycle.ps1 -LaunchClaude -AutoStash

# Claude 출력에서 task/patch를 저장한 뒤, 2단계: Gate만 실행
powershell -ExecutionPolicy Bypass -File .\scripts\mode_b_cycle.ps1 -TaskJson .\tasks\TYYYYMMDD-001.json -Patch .\patches\TYYYYMMDD-001.patch

# Gate까지만
powershell -ExecutionPolicy Bypass -File .\scripts\mode_b_cycle.ps1 -TaskJson .\tasks\TYYYYMMDD-001.json -Patch .\patches\TYYYYMMDD-001.patch

# 적용 + 커밋 + 푸시
powershell -ExecutionPolicy Bypass -File .\scripts\mode_b_cycle.ps1 -TaskJson .\tasks\TYYYYMMDD-001.json -Patch .\patches\TYYYYMMDD-001.patch -Apply -Commit -Push -CommitMessage "README: add (PROPOSED)"
```

---

## 4. Touch 허용 파일 목록(최소권한)

### 작업별 최소 허용(allow_patch_on_files)

| 작업 예시 | 허용 경로 |
|----------|-----------|
| README 첫 줄 수정 | `README.md` |
| README_AUTODEV 수정 | `README_AUTODEV.md` |
| docs 문서 수정 | `docs/*.md` |
| config 정책 수정 | `config/**/*.md` |

### 프로젝트 공통 allowlist(SSOT)

`.cursor/rules/000-core.mdc` 기준:

```
.cursor/
.github/
config/
docs/
tools/
tests/
pyproject.toml
plan.md
CODEOWNERS
README.md
CHANGELOG.md
MANIFEST.json
BATON_CURRENT.md
AGENTS.md
```

### Gate 2 검증 스크립트(최소권한)

README.md만 허용하는 예:

```powershell
$allowed = @("+++ b/README.md")
$touched = Select-String -Path .\patches\TYYYYMMDD-001.patch -Pattern "^\+\+\+ b/" | ForEach-Object { $_.Line }
$violation = $touched | Where-Object { $_ -notin $allowed }
if ($violation) { Write-Error "allowlist FAIL: $violation"; exit 1 }
```

---

## 5. 실패 시 즉시 처리(FAIL-SAFE)

### A) `git apply --check` FAIL

* **원인**: 컨텍스트 불일치/형식 오류/파일 발명
* **조치**: Claude에게 "README 실제 내용 기반" + "diff만"으로 재요청

### B) Claude가 설명/예시 섞음

* **조치**: "출력은 2블록만, 다른 텍스트 금지" 문구 유지 + `/quit` 후 재실행

### C) allowlist 위반

* **조치**: patch 폐기, task.json `allow_patch_on_files` 재확인

---

## 6. openclaw.json 마스킹(공유 시)

| 블록 | 마스킹 대상 |
|------|-------------|
| channels.telegram | botToken, allowFrom |
| gateway.auth | password, token |
| agents.list[].model | URL, API 키 |

---

## 참조

- [docs/CLAUDE_CODE_OLLAMA_WINDOWS_RUNBOOK.md](CLAUDE_CODE_OLLAMA_WINDOWS_RUNBOOK.md)
- [README_AUTODEV.md](../README_AUTODEV.md)
- [docs/STACK_SESSION_REPORT.md](../../docs/STACK_SESSION_REPORT.md)
