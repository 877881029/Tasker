from pathlib import Path

from tasker.__main__ import main

ROOT = Path(__file__).resolve().parents[1]


def test_help_exits_zero():
    assert main(["tasker", "--help"]) == 0


def test_frozen_shortcut_uses_exe_without_module_args():
    text = (ROOT / "src" / "tasker" / "__main__.py").read_text(encoding="utf-8")
    assert 'getattr(sys, "frozen", False)' in text
    assert 'return sys.executable, ()' in text
