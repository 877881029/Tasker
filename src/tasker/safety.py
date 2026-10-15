from __future__ import annotations

import ctypes
import os
import zipfile
from ctypes import wintypes
from datetime import datetime
from pathlib import Path

BACKUP_PREFIX = "tasker-"
BACKUP_KEEP = 7

FO_DELETE = 0x0003
FOF_SILENT = 0x0004
FOF_NOCONFIRMATION = 0x0010
FOF_ALLOWUNDO = 0x0040
FOF_NOERRORUI = 0x0400


class _SHFILEOPSTRUCTW(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("wFunc", wintypes.UINT),
        ("pFrom", wintypes.LPCWSTR),
        ("pTo", wintypes.LPCWSTR),
        ("fFlags", ctypes.c_ushort),
        ("fAnyOperationsAborted", wintypes.BOOL),
        ("hNameMappings", ctypes.c_void_p),
        ("lpszProgressTitle", wintypes.LPCWSTR),
    ]


def recycle_enabled() -> bool:
    value = os.environ.get("TASKER_NO_RECYCLE", "").strip().lower()
    return value not in {"1", "true", "yes", "on"}


def send_to_recycle_bin(path: Path) -> bool:
    """Move a file to the Windows Recycle Bin. Returns False if that is not possible."""
    target = Path(path)
    if not target.exists():
        return True
    try:
        shell32 = ctypes.windll.shell32
    except AttributeError:
        return False
    op = _SHFILEOPSTRUCTW()
    op.wFunc = FO_DELETE
    op.pFrom = str(target.resolve()) + "\0"
    op.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT | FOF_NOERRORUI
    result = shell32.SHFileOperationW(ctypes.byref(op))
    return result == 0 and not op.fAnyOperationsAborted and not target.exists()


def remove_file(path: Path) -> None:
    target = Path(path)
    if not target.exists():
        return
    if recycle_enabled() and send_to_recycle_bin(target):
        return
    target.unlink()


def default_backup_dir() -> Path:
    override = os.environ.get("TASKER_BACKUP_DIR", "").strip()
    if override:
        return Path(override).expanduser()
    try:
        from PySide6.QtCore import QStandardPaths

        docs = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DocumentsLocation
        )
    except Exception:
        docs = ""
    base = Path(docs) if docs else Path.home() / "Documents"
    return base / "Tasker" / "backups"


def list_backups(dest: Path) -> list[Path]:
    folder = Path(dest)
    if not folder.is_dir():
        return []
    return sorted(folder.glob(f"{BACKUP_PREFIX}*.zip"))


def backup_tasks(root: Path, dest: Path, keep: int = BACKUP_KEEP, now: datetime | None = None) -> Path:
    moment = now or datetime.now()
    folder = Path(dest)
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{BACKUP_PREFIX}{moment:%Y%m%d-%H%M%S}.zip"
    tasks = Path(root) / "tasks"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        if tasks.is_dir():
            for path in sorted(tasks.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(root).as_posix())
        settings = Path(root) / "settings.json"
        if settings.is_file():
            archive.write(settings, "settings.json")
    backups = list_backups(folder)
    for old in backups[: max(0, len(backups) - keep)]:
        try:
            old.unlink()
        except OSError:
            pass
    return target


def daily_backup(root: Path, dest: Path, now: datetime | None = None) -> Path | None:
    moment = now or datetime.now()
    stamp = f"{BACKUP_PREFIX}{moment:%Y%m%d}"
    if any(path.name.startswith(stamp) for path in list_backups(dest)):
        return None
    return backup_tasks(root, dest, now=moment)
