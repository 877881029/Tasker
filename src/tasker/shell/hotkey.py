from __future__ import annotations

import ctypes
from collections.abc import Callable
from ctypes import wintypes

from PySide6.QtCore import QAbstractNativeEventFilter, QCoreApplication

WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000
VK_T = 0x54

CANDIDATES: tuple[tuple[int, int, str], ...] = (
    (MOD_WIN | MOD_ALT, VK_T, "Win+Alt+T"),
    (MOD_CONTROL | MOD_ALT, VK_T, "Ctrl+Alt+T"),
)


class GlobalHotkey(QAbstractNativeEventFilter):
    """Registers the first free combination in CANDIDATES as a system-wide hotkey."""

    HOTKEY_ID = 0x7A51

    def __init__(self, on_trigger: Callable[[], None]) -> None:
        super().__init__()
        self._on_trigger = on_trigger
        self.label = ""
        self._installed = False

    def register(self, candidates=CANDIDATES) -> str:
        try:
            user32 = ctypes.windll.user32
        except AttributeError:
            return ""
        for mods, vk, label in candidates:
            if user32.RegisterHotKey(None, self.HOTKEY_ID, mods | MOD_NOREPEAT, vk):
                self.label = label
                app = QCoreApplication.instance()
                if app is not None and not self._installed:
                    app.installNativeEventFilter(self)
                    self._installed = True
                return label
        return ""

    def unregister(self) -> None:
        if self.label:
            try:
                ctypes.windll.user32.UnregisterHotKey(None, self.HOTKEY_ID)
            except AttributeError:
                pass
            self.label = ""
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
