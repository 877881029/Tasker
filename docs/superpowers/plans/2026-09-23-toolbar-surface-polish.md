# Toolbar surface polish implementation plan

**Goal:** Make Tasker's first row feel intentionally designed rather than assembled
from stock Qt controls, without changing behavior or locked product contracts.

**Architecture:** Keep the public `QLineEdit` contract, existing `QToolButton`
objects, and signal wiring. A private `SearchLineEdit` painter owns only the search
surface because the Windows style otherwise forces a native focus underline and
white base; geometry, palette, accessibility, and behavior remain unchanged.

## Task 1: Lock the new toolbar contract in tests

**Files:** `tests/test_window.py`, `tests/test_ui_contract.py`

- Assert search height, placeholder color, and tool hit target dimensions.
- Assert QSS contains the inset search surface, 12px radius, complete 2px focus
  ring, 10px tool radius, and hover/checked/pressed treatments.
- Assert existing object names, accessible names, and tab order remain intact.

- [x] Failing tests
- [x] Commit and push

## Task 2: Implement the unified first row

**Files:** `src/tasker/shell/window.py`, `src/tasker/theme.py`, `DESIGN.md`

- Set 14px row margins and 8px spacing.
- Set search to 38px and tools to 36px.
- Apply an explicit muted placeholder palette.
- Replace stock-like search and bare tool styles with the approved paper surfaces.
- Update the documented component dimensions and states.

- [x] Implementation
- [x] Targeted tests pass
- [x] Commit and push

## Task 3: Release verification

**Files:** `docs/STATUS.md`, this plan

- Run `tests/test_window.py`, `tests/test_ui_contract.py`, then the full suite.
- Stop the deployed Tasker, rebuild the frozen package, deploy it to the stable
  local program path, and overwrite the desktop shortcut.
- Capture the collapsed first row at 150% scaling and compare against the user
  screenshot.

- [x] Full suite passes (`93 passed`, Python 3.12, exit code 0)
- [x] Native screenshot accepted against specification at 150% DPI
- [x] Frozen package rebuilt and desktop shortcut refreshed
- [x] STATUS completed
- [x] Final commit and push
