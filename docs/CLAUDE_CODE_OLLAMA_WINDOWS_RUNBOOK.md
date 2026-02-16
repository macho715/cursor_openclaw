# Claude Code + Ollama Windows Runbook

## Scope

- Target OS: Windows native (no WSL path)
- Ollama mode: local app
- Primary model: `kwangsuklee/SEOKDONG-llama3.1_korean_Q5_K_M`
- Fallback model: `exaone3.5:7.8b`
- Operating mode default: `Mode B` (Claude = task + diff proposal, Cursor = apply only)

## 1) Install/Verify

```powershell
ollama --version
ollama list
irm https://claude.ai/install.ps1 | iex
claude --version
```

Expected:

- `ollama --version` returns without client/server mismatch warning
- `ollama list` includes both primary/fallback models
- `claude --version` prints installed version

## 2) Link Claude Code to Ollama

Interactive:

```powershell
ollama launch
```

Direct launch with model:

```powershell
ollama launch claude --model kwangsuklee/SEOKDONG-llama3.1_korean_Q5_K_M
```

Non-interactive smoke check:

```powershell
ollama launch claude --model kwangsuklee/SEOKDONG-llama3.1_korean_Q5_K_M -- -p "Respond with exactly: OLLAMA_OK"
```

## 3) Minimal Repo Validation

Run from repo root:

```powershell
cd C:\Users\jichu\Downloads\cursor_full_setting_optionA\cursor_openclaw
ollama launch claude --model kwangsuklee/SEOKDONG-llama3.1_korean_Q5_K_M -- -p "In this repo, propose a one-line README change as unified diff only. Do not apply changes."
```

Expected:

- Claude returns a proposed unified diff
- No automatic apply/commit

## 3.1) Mode B Rules (Mandatory)

SSOT for acceptance is always local git output.

1. Claude output is accepted only as:
- `task.json`
- `unified diff`
2. If output includes explanations/examples/fake git-status snippets, discard immediately.
3. Every proposed diff must pass local verification:
- `git apply --check <patch>`
4. Before check passes, `git apply` is forbidden.
5. Touched files outside allowlist are immediate fail.
6. If repo is dirty, secure baseline first (`stash` or equivalent) before cycle.
7. Prompt must force "read real file content, modify existing lines only, no hallucination."
8. Final apply/test/commit is Cursor control-plane only.

Validation sequence:

```powershell
git status --porcelain
# run claude/ollama request and save patch
git apply --check .\candidate.patch
git status --porcelain
```

Pass criteria:

- `git apply --check` succeeds
- pre/post `git status --porcelain` delta is `0` (unless you intentionally apply)

## 3.2) Mode B One-Cycle (10 min)

0) Baseline

```powershell
cd C:\Users\jichu\Downloads\cursor_full_setting_optionA\cursor_openclaw
git status --porcelain
```

If dirty:

```powershell
git stash push -u -m "WIP before ModeB"
git status --porcelain
```

1) Launch Claude on Ollama

```powershell
ollama launch claude --model kwangsuklee/SEOKDONG-llama3.1_korean_Q5_K_M:latest
```

2) Prompt template (strict output)

```text
In this repo, add only ` (PROPOSED)` to the end of the first line of README.md.
You must read the real README.md and modify existing content only. No hallucination.
Output only the two blocks below and nothing else:
---BEGIN_TASK_JSON---
(task.json)
---END_TASK_JSON---
---BEGIN_PATCH---
(git-applyable unified diff; only README.md; one changed line total)
---END_PATCH---
Final line must be exactly: GIT_STATUS_DELTA_EXPECTED=0
```

3) Save outputs

```powershell
mkdir tasks, patches -Force | Out-Null
# Save task block to tasks\TYYYYMMDD-001.json
# Save patch block to patches\TYYYYMMDD-001.patch
```

4) Gate 1: patch applicability

```powershell
git apply --check .\patches\TYYYYMMDD-001.patch
echo $LASTEXITCODE
```

5) Gate 2: allowlist/touched files

```powershell
python .\scripts\gate_local.py .\patches\TYYYYMMDD-001.patch .\tasks\TYYYYMMDD-001.json
```

6) Cursor-only apply

```powershell
git apply .\patches\TYYYYMMDD-001.patch
git status --porcelain
git commit -am "README: add (PROPOSED)"
git push
```

Fail-safe:

- If `git apply --check` fails: discard patch, regenerate.
- If non-diff text is mixed in output: discard and restart session.

## 4) Operating Model (Queue Role Separation)

- Claude Code: requirement shaping + task draft only
- OpenClaw worker: patch generation only
- Cursor control-plane: apply/test/commit/PR/merge only

Queue flow:

- Input ticket: `.autodev_queue/inbox/*.json`
- Gate/decision path: DRY_RUN -> DIFF -> GATE -> DECIDE
- Only Cursor executes final apply and merge actions

## 5) Security Hardening Checklist

- Rotate exposed external tokens at provider side
- Keep Telegram channel disabled until new token is issued
- Regenerate gateway auth token and restart services that consume it

Note:

- Local config rotation does not revoke external bot tokens. Revoke/regenerate from the source service.
