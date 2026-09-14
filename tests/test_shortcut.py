from __future__ import annotations

import subprocess
from pathlib import Path

from tasker.identity import APP_USER_MODEL_ID
from tasker.shell.shortcut import _icon_location, create_desktop_shortcut


class FakeShortcut:
    def __init__(self) -> None:
        self.Targetpath = ""
        self.Arguments = ""
        self.WorkingDirectory = ""
        self.Description = ""
        self.IconLocation = ""
        self.saved = False

    def Save(self) -> None:
        self.saved = True


class FakeWScriptShell:
    def __init__(self) -> None:
        self.shortcuts: list[FakeShortcut] = []

    def CreateShortCut(self, path: str) -> FakeShortcut:
        shortcut = FakeShortcut()
        self.shortcuts.append(shortcut)
        return shortcut


class FakeComModule:
    def __init__(self) -> None:
        self.shell = FakeWScriptShell()

    def Dispatch(self, prog_id: str) -> FakeWScriptShell:
        assert prog_id == "WScript.Shell"
        return self.shell


def test_icon_location_quotes_and_index():
    assert _icon_location(r"C:\Tasker\Tasker.exe") == r"C:\Tasker\Tasker.exe,0"
    assert (
        _icon_location(r"C:\Program Files\Tasker\Tasker.exe")
        == r'"C:\Program Files\Tasker\Tasker.exe",0'
    )


def test_create_desktop_shortcut_uses_known_location(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("tasker.shell.shortcut._desktop_known_location", lambda: tmp_path / "KnownDesktop")
    com = FakeComModule()
    ico = r"C:\Tasker\assets\icons\tasker.ico"

    path = create_desktop_shortcut(
        r"C:\Tasker\dist\Tasker\Tasker.exe",
        winshell_or_com=com,
        icon=ico,
    )

    assert path == tmp_path / "KnownDesktop" / "Tasker.lnk"
    shortcut = com.shell.shortcuts[0]
    assert shortcut.Targetpath == r"C:\Tasker\dist\Tasker\Tasker.exe"
    assert shortcut.Arguments == ""
    assert shortcut.WorkingDirectory == r"C:\Tasker\dist\Tasker"
    assert shortcut.IconLocation == ico + ",0"
    assert shortcut.Description == "Tasker"
    assert shortcut.saved is True


def test_create_desktop_shortcut_falls_back_userprofile(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("tasker.shell.shortcut._desktop_known_location", lambda: None)
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    com = FakeComModule()

    path = create_desktop_shortcut(
        r"C:\Tasker\Tasker.exe",
        name="Tasker App",
        winshell_or_com=com,
    )

    assert path == tmp_path / "Desktop" / "Tasker App.lnk"


def test_create_desktop_shortcut_sets_app_user_model_id(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("tasker.shell.shortcut._desktop_known_location", lambda: tmp_path / "KnownDesktop")
    com = FakeComModule()
    seen: list[tuple[Path, str]] = []

    path = create_desktop_shortcut(
        r"C:\Tasker\Tasker.exe",
        winshell_or_com=com,
        app_id_setter=lambda shortcut, app_id: seen.append((shortcut, app_id)),
    )

    assert seen == [(path, APP_USER_MODEL_ID)]


def test_create_desktop_shortcut_preserves_existing(monkeypatch, tmp_path: Path) -> None:
    desktop = tmp_path / "KnownDesktop"
    desktop.mkdir()
    existing = desktop / "Tasker.lnk"
    existing.write_bytes(b"user shortcut")
    monkeypatch.setattr("tasker.shell.shortcut._desktop_known_location", lambda: desktop)
    com = FakeComModule()

    result = create_desktop_shortcut(r"C:\Tasker\Tasker.exe", winshell_or_com=com)

    assert result == existing
    assert existing.read_bytes() == b"user shortcut"
    assert com.shell.shortcuts == []


def test_create_desktop_shortcut_overwrite_recreates(monkeypatch, tmp_path: Path) -> None:
    desktop = tmp_path / "KnownDesktop"
    desktop.mkdir()
    (desktop / "Tasker.lnk").write_bytes(b"old")
    monkeypatch.setattr("tasker.shell.shortcut._desktop_known_location", lambda: desktop)
    com = FakeComModule()

    create_desktop_shortcut(r"C:\Tasker\Tasker.exe", winshell_or_com=com, overwrite=True)

    assert len(com.shell.shortcuts) == 1
    assert com.shell.shortcuts[0].saved is True


def test_create_desktop_shortcut_list2cmdline(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("tasker.shell.shortcut._desktop_known_location", lambda: tmp_path / "KnownDesktop")
    com = FakeComModule()
    args = ("-m", "tasker")

    create_desktop_shortcut(r"C:\Python\python.exe", args=args, winshell_or_com=com)

    assert com.shell.shortcuts[0].Arguments == subprocess.list2cmdline(list(args))
