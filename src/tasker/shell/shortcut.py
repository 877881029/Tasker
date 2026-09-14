from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Callable

from tasker.identity import APP_USER_MODEL_ID


def create_desktop_shortcut(
    exe: str,
    name: str = "Tasker",
    winshell_or_com=None,
    *,
    args: tuple[str, ...] = (),
    icon: str | None = None,
    overwrite: bool = False,
    app_id_setter: Callable[[Path, str], None] | None = None,
) -> Path:
    from pathlib import Path as P

    desktop = P.home() / "Desktop"
    desktop.mkdir(parents=True, exist_ok=True)
    shortcut_path = desktop / f"{name}.lnk"
    if shortcut_path.exists() and not overwrite:
        return shortcut_path
    if winshell_or_com is None:
        import win32com.client as winshell_or_com

    shell = winshell_or_com.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(str(shortcut_path))
    shortcut.Targetpath = exe
    shortcut.Arguments = subprocess.list2cmdline(list(args)) if args else ""
    shortcut.WorkingDirectory = str(P(exe).parent)
    shortcut.Description = name
    shortcut.IconLocation = icon or exe
    save = getattr(shortcut, "Save", None) or getattr(shortcut, "save")
    save()
    if app_id_setter is not None:
        app_id_setter(shortcut_path, APP_USER_MODEL_ID)
    return shortcut_path
