
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


SSOT_CANDIDATES = [
    'AGENTS.md',
    'config/policy/CURSOR_RULES.md',
]


def test_ssot_reference_exists():
    assert any(Path(p).exists() for p in SSOT_CANDIDATES), (
        f"Missing SSOT reference candidates: {SSOT_CANDIDATES}"
    )
