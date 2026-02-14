
from pathlib import Path

REQUIRED = [
  'config/policy/CURSOR_RULES.md',
  'config/policy/TOOL_POLICY.md',
  'config/policy/APPROVAL_MATRIX.md',
  'config/policy/AUDIT_LOG_SCHEMA.md',
  'config/uiux/SCREENS.md',
  'config/uiux/INPUT_GUARD.md',
  'config/uiux/A11Y_DoD.md',
  'config/uiux/COPY.md',
  'config/uiux/COMPONENTS.md',
  '.cursor/rules/000-core.mdc',
  '.cursor/rules/050-ux-a11y.mdc',
  '.cursor/skills/incident-stop/SKILL.md',
]

def test_assets_exist():
    missing = [p for p in REQUIRED if not Path(p).exists()]
    assert not missing, f"Missing: {missing}"
