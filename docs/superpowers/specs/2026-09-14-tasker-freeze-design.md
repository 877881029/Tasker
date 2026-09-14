# Tasker frozen Windows build

Date: 2026-09-14  
Status: Approved by user (“开始开发”; same local-run model as Reader)  
Progress ledger: `docs/STATUS.md`

## 1. Goal

Colleagues and the owner double-click `dist\Tasker\Tasker.exe` (or the desktop shortcut) after one `scripts\setup.ps1`, without Docker and without remembering `python -m tasker`.

## 2. Architecture

- `tasker.spec`: PyInstaller **onedir**, `console=False`, icon `assets/icons/tasker.ico`, collect PySide6 WebEngine process + Tasker icons. No pptx/md Vite bundles.
- `scripts/build_windows.ps1`: venv pip `.[dev]` + pyinstaller, `generate_icons.py`, clean `build/` `dist/`, `PyInstaller tasker.spec`.
- `scripts/setup.ps1`: after install, run `build_windows.ps1` unless `-SkipBuild`; launch frozen exe when present, else `-m tasker`. `-SkipLaunch` still skips the window.
- Frozen `__main__` shortcut target is `Tasker.exe` with no `-m tasker` args.

## 3. Non-goals

- Changing dock/detail behavior.
- Bundling Vikunja or adding Docker.
- Committing `dist/` or `build/`.
