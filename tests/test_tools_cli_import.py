import importlib
import sys


def test_import_tools_cli_does_not_mutate_sys_path() -> None:
    original_path = list(sys.path)

    sys.modules.pop("tools.cli", None)
    importlib.import_module("tools.cli")

    assert sys.path == original_path
