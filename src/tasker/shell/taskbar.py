from __future__ import annotations

import ctypes
import os
import sys
from pathlib import Path

from tasker.identity import APP_USER_MODEL_ID

DWMWA_FORCE_ICONIC_REPRESENTATION = 7
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWCP_ROUND = 2
WM_SETICON = 0x0080
ICON_SMALL = 0
ICON_BIG = 1
IMAGE_ICON = 1
LR_LOADFROMFILE = 0x0010


def force_iconic_representation(hwnd: int) -> bool:
    if os.name != "nt" or hwnd == 0:
        return False
    value = ctypes.c_int(1)
    try:
        result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_FORCE_ICONIC_REPRESENTATION,
            ctypes.byref(value),
            ctypes.sizeof(value),
        )
    except Exception:
        return False
    return int(result) == 0


def apply_rounded_corners(hwnd: int) -> bool:
    if os.name != "nt" or hwnd == 0:
        return False
    value = ctypes.c_int(DWMWCP_ROUND)
    try:
        result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_WINDOW_CORNER_PREFERENCE,
            ctypes.byref(value),
            ctypes.sizeof(value),
        )
    except Exception:
        return False
    return int(result) == 0


def apply_hwnd_app_user_model(hwnd: int, icon_path: Path) -> bool:
    if os.name != "nt" or hwnd == 0:
        return False
    try:
        from win32com.propsys import propsys, pscon
    except ImportError:
        return False
    resolved_icon = Path(icon_path).resolve()
    if getattr(sys, "frozen", False):
        command = f'"{sys.executable}"'
        icon_res = f"{sys.executable},0"
    else:
        command = f'"{sys.executable}" -m tasker'
        icon_res = f"{resolved_icon},0"
    try:
        store = propsys.SHGetPropertyStoreForWindow(hwnd)
        store.SetValue(
            pscon.PKEY_AppUserModel_ID,
            propsys.PROPVARIANTType(APP_USER_MODEL_ID),
        )
        store.SetValue(
            pscon.PKEY_AppUserModel_RelaunchCommand,
            propsys.PROPVARIANTType(command),
        )
        store.SetValue(
            pscon.PKEY_AppUserModel_RelaunchIconResource,
            propsys.PROPVARIANTType(icon_res),
        )
        store.SetValue(
            pscon.PKEY_AppUserModel_RelaunchDisplayNameResource,
            propsys.PROPVARIANTType("Tasker"),
        )
        store.Commit()
        return True
    except Exception:
        return False


def apply_taskbar_icon(hwnd: int, icon_path: Path) -> bool:
    if os.name != "nt" or hwnd == 0 or not Path(icon_path).exists():
        return False
    user32 = ctypes.windll.user32
    path = str(Path(icon_path).resolve())
    small = user32.LoadImageW(None, path, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)
    big = user32.LoadImageW(None, path, IMAGE_ICON, 32, 32, LR_LOADFROMFILE)
    if small:
        user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, small)
    if big:
        user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, big)
    force_iconic_representation(hwnd)
    apply_rounded_corners(hwnd)
    apply_hwnd_app_user_model(hwnd, Path(icon_path))
    return bool(small or big)
