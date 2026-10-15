from __future__ import annotations

import ctypes
from collections.abc import Callable, Iterable
from ctypes import wintypes

from PySide6.QtCore import QAbstractNativeEventFilter, QCoreApplication

from tasker.settings import GLOBAL_FALLBACKS

WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000
VK_T = 0x54

_MODS = {"ctrl": MOD_CONTROL, "alt": MOD_ALT, "shift": MOD_SHIFT, "win": MOD_WIN, "meta": MOD_WIN}


def parse_combo(text: str) -> tuple[int, int] | None:
    """Turn 'Win+Alt+T' into (modifiers, virtual-key). Letters, digits and F1-F24 only."""
    parts = [part.strip() for part in (text or "").split("+") if part.strip()]
    if not parts:
        return None
    mods = 0
    for part in parts[:-1]:
        flag = _MODS.get(part.casefold())
        if flag is None:
            return None
        mods |= flag
    key = parts[-1].upper()
    if len(key) == 1 and (key.isascii() and key.isalnum()):
        vk = ord(key)
    elif key.startswith("F") and key[1:].isdigit() and 1 <= int(key[1:]) <= 24:
        vk = 0x70 + int(key[1:]) - 1
    else:
        return None
    if mods == 0 and not key.startswith("F"):
        return None
    return mods, vk


CANDIDATES: tuple[tuple[int, int, str], ...] = tuple(
    (*parse_combo(label), label) for label in GLOBAL_FALLBACKS  # type: ignore[misc]
)


class GlobalHotkey(QAbstractNativeEventFilter):
    """Registers one system-wide hotkey and calls on_trigger when it fires."""

    HOTKEY_ID = 0x7A51

    def __init__(self, on_trigger: Callable[[], None]) -> None:
        super().__init__()
        self._on_trigger = on_trigger
        self.label = ""
        self._installed = False

    def _install(self) -> None:
        app = QCoreApplication.instance()
        if app is not None and not self._installed:
            app.installNativeEventFilter(self)
            self._installed = True

    def _try(self, mods: int, vk: int) -> bool:
        try:
            user32 = ctypes.windll.user32
        except AttributeError:
            return False
        return bool(user32.RegisterHotKey(None, self.HOTKEY_ID, mods | MOD_NOREPEAT, vk))

    def _release(self) -> None:
        if self.label:
            try:
                ctypes.windll.user32.UnregisterHotKey(None, self.HOTKEY_ID)
            except AttributeError:
                pass
            self.label = ""

    def register(self, candidates: Iterable[tuple[int, int, str]] = CANDIDATES) -> str:
        self._release()
        for mods, vk, label in candidates:
            if self._try(mods, vk):
                self.label = label
                self._install()
                return label
        return ""

    def register_text(self, text: str) -> str:
        """Bind `text` ('' = automatic fallback). Keeps the previous binding on failure."""
        if not text:
            return self.register()
        combo = parse_combo(text)
        if combo is None:
            return ""
        previous = self.label
        self._release()
        if self._try(*combo):
            self.label = text
            self._install()
            return text
        if previous:
            restored = parse_combo(previous)
            if restored is not None and self._try(*restored):
                self.label = previous
        return ""

    def unregister(self) -> None:
        self._release()
        app = QCoreApplication.instance()
        if app is not None and self._installed:
            app.removeNativeEventFilter(self)
            self._installed = False

    def nativeEventFilter(self, event_type, message):
        raw = event_type.data() if hasattr(event_type, "data") else bytes(event_type)
        if self.label and raw in {b"windows_dispatcher_MSG", b"windows_generic_MSG"}:
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == WM_HOTKEY and msg.wParam == self.HOTKEY_ID:
                self._on_trigger()
                return True, 0
        return False, 0
