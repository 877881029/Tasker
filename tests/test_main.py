from pathlib import Path

from tasker.__main__ import _launch_target, main

ROOT = Path(__file__).resolve().parents[1]


def test_help_exits_zero():
    assert main(["tasker", "--help"]) == 0


def test_frozen_shortcut_uses_exe_without_module_args():
    text = (ROOT / "src" / "tasker" / "__main__.py").read_text(encoding="utf-8")
    assert 'getattr(sys, "frozen", False)' in text
    assert 'return sys.executable, ()' in text


def test_launch_target_prefers_frozen_dist_exe(monkeypatch, tmp_path: Path):
    fake = tmp_path / "Tasker.exe"
    fake.write_bytes(b"mz")
    monkeypatch.setattr("tasker.__main__.frozen_exe_path", lambda: fake)
    monkeypatch.setattr("sys.frozen", False, raising=False)
    exe, args = _launch_target()
    assert exe == str(fake)
    assert args == ()
