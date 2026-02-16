# Claude Code + Ollama Windows Runbook

## Scope

- Target OS: Windows native (no WSL path)
- Ollama mode: local app
- Primary model: `kwangsuklee/SEOKDONG-llama3.1_korean_Q5_K_M`
- Fallback model: `exaone3.5:7.8b`

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

