from __future__ import annotations

from pathlib import Path
import os


def data_dir() -> Path:
    override = os.environ.get("TASKER_DATA_DIR", "").strip()
    if override:
        path = Path(override).expanduser().resolve()
    else:
        local = os.environ.get("LOCALAPPDATA", "").strip()
        root = Path(local) if local else Path.home() / "AppData" / "Local"
        path = (root / "Tasker").resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def db_path() -> Path:
    return data_dir() / "tasker.sqlite"


def attachments_dir(item_id: str) -> Path:
    path = data_dir() / "attachments" / item_id
    path.mkdir(parents=True, exist_ok=True)
    return path
