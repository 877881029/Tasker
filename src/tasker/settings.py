from __future__ import annotations

import json
from pathlib import Path

FILE_NAME = "settings.json"


def load_settings(root: Path) -> dict:
    path = Path(root) / FILE_NAME
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def save_setting(root: Path, key: str, value) -> None:
    data = load_settings(root)
    data[key] = value
    path = Path(root) / FILE_NAME
    try:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass
