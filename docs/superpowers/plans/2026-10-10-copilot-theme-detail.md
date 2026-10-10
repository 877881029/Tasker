# Copilot theme and detail experience plan

Spec: `docs/superpowers/specs/2026-10-10-copilot-theme-detail-design.md`

## Task 1: Theme tokens and shell (TDD)

Files: `src/tasker/theme.py`, `tests/test_ui_contract.py`, `DESIGN.md`

- Lock new token values, new `HOVER`/`SELECTED`/`LINE_STRONG`/`UI_FONT`, 10px shell, neutral `card_style`.
- `dock_style`: rail `CHROME`, detail `PAPER`, 1px `LINE` shell border, no cobalt bubble, ghost tools, menu style.

- [x] Tests updated first, then implementation

## Task 2: Rail, rows, toolbar

Files: `src/tasker/shell/window.py`, `tests/test_window.py`

- Search 34px / 8px; tools 32px ghost; notch → 1px divider.
- Rows: 40px min, 10px dot, hover/selected fills, right-click status menu.
- `open_detail` updates selection without rebuilding the list.

- [x] Tests, implementation

## Task 3: Status pill, title, delete, footer

Files: `src/tasker/shell/status.py` (new), `src/tasker/shell/detail.py`, `tests/test_detail.py`

- `apply_status(store, item_id, target)` via `set_done` / `cycle_color`.
- Header: status pill menu, borderless title, trash ghost with two-step confirm.
- Footer status line with write indicator and saved time.

- [x] Tests, implementation

## Task 4: Journal typography

Files: `src/tasker/shell/journal_edit.py`, `src/tasker/theme.py`, tests

- Segoe UI / Microsoft YaHei UI 15px, line-height 1.65 in both Chromium and editor.

- [x] Tests, implementation

## Task 5: Release

- [x] Full suite passes, exit 0
- [x] 150% DPI native screenshots (collapsed, read, write, status menu, delete confirm)
- [x] Frozen build, deploy, desktop shortcut overwrite
- [x] STATUS complete, push
