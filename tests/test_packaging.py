from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_tasker_spec_onedir_icon_and_webengine() -> None:
    spec = (ROOT / "tasker.spec").read_text(encoding="utf-8")
    normalized = spec.replace("\\", "/")
    assert "name='Tasker'" in spec
    assert "console=False" in spec
    assert "COLLECT(" in spec
    assert "assets/icons/tasker.ico" in normalized
    assert "assets/icons/tasker-t.svg" in normalized
    assert "assets/icons/add.svg" in normalized
    assert "assets/icons/hide.svg" in normalized
    assert "assets/icons/pin.svg" in normalized
    assert "QtSvg" in spec
    assert "QtWebEngineProcess.exe" in spec
    assert 'collect_submodules(\'PySide6.QtWebEngineWidgets\')' in spec
    assert "VERSION" in spec and "assets/icons/tasker.ico" in normalized


def test_build_windows_script_runs_tasker_spec() -> None:
    script = (ROOT / "scripts" / "build_windows.ps1").read_text(encoding="utf-8")
    assert "TASKER_BUILD_VENV" in script
    assert "Join-Path $VenvPath \"Scripts\\python.exe\"" in script
    assert '& $Python -m pip install -e ".[dev]" pyinstaller' in script
    assert '& $Python scripts\\generate_icons.py' in script
    assert (
        "& $Python -m PyInstaller tasker.spec --noconfirm --clean "
        "--distpath $DistPath --workpath $WorkPath"
    ) in script
    assert "dist\\Tasker\\Tasker.exe" in script
    assert "docker" not in script.lower()
    assert "vikunja" not in script.lower()


def test_setup_ps1_freezes_unless_skip_build() -> None:
    text = (ROOT / "scripts" / "setup.ps1").read_text(encoding="utf-8")
    assert "SkipBuild" in text
    assert "build_windows.ps1" in text
    assert "dist\\Tasker\\Tasker.exe" in text
    assert "-m tasker" in text
    assert "docker" not in text.lower()
