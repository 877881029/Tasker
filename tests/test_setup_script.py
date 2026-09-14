from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_setup_ps1_installs_editable_and_launches_module():
    text = (ROOT / "scripts" / "setup.ps1").read_text(encoding="utf-8")
    assert "pip install -e" in text
    assert "-m tasker" in text
    assert "docker" not in text.lower()
    assert "vikunja" not in text.lower()
    assert "build_windows" not in text
