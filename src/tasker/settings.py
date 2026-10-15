from __future__ import annotations

import json
from pathlib import Path

FILE_NAME = "settings.json"

DEFAULTS: dict = {
    "show_summary": False,
    "reminders": True,
    "auto_backup": True,
}

# action -> (label, description, default key, scope)
SHORTCUTS: dict[str, tuple[str, str, str, str]] = {
    "quick_capture": ("快速记录", "在任何程序里弹出输入框，回车即记下一条任务", "", "global"),
    "new": ("新建任务", "新建一条任务并打开详情", "Ctrl+N", "dock"),
    "search": ("查找", "跳到搜索框", "Ctrl+F", "dock"),
    "undo": ("撤销删除", "删除后 5 秒内恢复", "Ctrl+Z", "dock"),
    "report": ("复制本周周报", "把本周日志汇总成 Markdown 复制到剪贴板", "Ctrl+Shift+C", "dock"),
    "write": ("写入日志", "在详情里新增一条带时间戳的日志", "Ctrl+I", "detail"),
    "save": ("保存日志", "保存并回到只读视图", "Ctrl+S", "detail"),
}

# An empty quick_capture means: try Win+Alt+T, then Ctrl+Alt+T.
GLOBAL_FALLBACKS = ("Win+Alt+T", "Ctrl+Alt+T")

FIXED_KEYS: tuple[tuple[str, str], ...] = (
    ("Enter / 空格", "打开选中的任务"),
    ("↑ / ↓", "在搜索框和任务之间移动"),
    ("Del", "删除选中的任务（进入回收站，5 秒内可撤销）"),
    ("Esc", "收起详情；详情未打开时隐藏到托盘（钉住时不隐藏）"),
    ("右键 / 菜单键", "改状态、设置 DDL"),
)

RESERVED_KEYS = {"Esc", "Return", "Enter", "Space", "Del", "Delete", "Up", "Down", "Tab", "Backspace"}


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


def get_setting(root: Path, key: str):
    return load_settings(root).get(key, DEFAULTS.get(key))


def shortcut_map(root: Path) -> dict[str, str]:
    stored = load_settings(root).get("shortcuts", {})
    stored = stored if isinstance(stored, dict) else {}
    return {action: str(stored.get(action, spec[2])) for action, spec in SHORTCUTS.items()}


def save_shortcut(root: Path, action: str, keys: str) -> None:
    data = load_settings(root)
    stored = data.get("shortcuts", {})
    stored = dict(stored) if isinstance(stored, dict) else {}
    if keys == SHORTCUTS[action][2]:
        stored.pop(action, None)
    else:
        stored[action] = keys
    save_setting(root, "shortcuts", stored)


def reset_shortcuts(root: Path) -> None:
    save_setting(root, "shortcuts", {})


def shortcut_conflict(mapping: dict[str, str], action: str, keys: str) -> str | None:
    """Return a user-facing reason why `keys` can't be bound to `action`, or None."""
    if not keys:
        return None
    parts = keys.split("+")
    if len(parts) == 1:
        if parts[0] in RESERVED_KEYS:
            return f"{keys} 已固定用于列表操作"
        if not (parts[0].startswith("F") and parts[0][1:].isdigit()):
            return "需要配合 Ctrl / Alt / Shift / Win 使用"
    for other, current in mapping.items():
        if other != action and current and current.casefold() == keys.casefold():
            return f"与「{SHORTCUTS[other][0]}」冲突"
    return None
