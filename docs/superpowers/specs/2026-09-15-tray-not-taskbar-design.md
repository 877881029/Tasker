# Tasker 托盘工作台，不占任务栏按钮

Date: 2026-09-15  
Status: Approved from user copy (workbench lives in 任务栏 Hide / notification overflow, not as a pinned taskbar app)  
Progress ledger: `docs/STATUS.md`

## Goal

Tasker is a workbench, not a document window. While running it must **not** occupy a regular taskbar button. Presence is a **system tray** icon (Windows may put it in the overflow / 隐藏的图标; that Hide list is a user setting we cannot force).

## Behavior

- Dock flags: `Qt.Tool | FramelessWindowHint` (plus pin → `WindowStaysOnTopHint`). No `Qt.Window` taskbar app.
- `QSystemTrayIcon` with Tasker ico. Left/double-click or 显示: raise dock. 退出: quit the process.
- Dock × hides the dock; process stays in the tray. `QApplication.setQuitOnLastWindowClosed(False)`.
- Do not call `apply_taskbar_icon` / AppUserModel relaunch on the dock hwnd (that re-creates a taskbar button).
- Second-instance ping still `show_dock`.
