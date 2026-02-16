# Orchestrator (MVP)

Minimal Python orchestrator that:
- reads config from `config.yaml`
- builds a patch prompt from `prompts/claude_patch_prompt.txt`
- calls Claude/Ollama command
- writes patch/report artifacts
- enforces local gate with `git apply --check`
- sends Telegram notification (optional)

## Setup

```powershell
cd orchestrator
python -m pip install -r requirements.txt
```

Update `config.yaml` placeholders:
- `telegram.bot_token`
- `telegram.chat_id`
- `repository.root_path`

Or use env overrides:
- `ORCH_TELEGRAM_BOT_TOKEN`
- `ORCH_TELEGRAM_CHAT_ID`
- `ORCH_REPO_ROOT`

## Run

```powershell
cd orchestrator
python main.py
```

Enter `/work` text when prompted.

One-shot mode:

```powershell
python main.py --work-text "README first line append (PROPOSED)"
```

Telegram polling mode (Updater):

```powershell
python main.py --polling
```

Telegram commands:
- `/start`
- `/work <instruction>`

## Notes

- If token/chat_id placeholders remain, Telegram send is skipped.
- The model command must output unified diff to stdout.
- Final apply/commit must be done in Cursor control-plane.
