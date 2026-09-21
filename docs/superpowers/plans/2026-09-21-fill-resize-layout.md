# Fill-resize layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the Tasker paper window fill the work area and still resize from all eight edges, with the rail fixed on the right and detail stretching.

**Architecture:** Pure helpers (`paper_corner_radius`, `hit_test_local`) own the math. `DockWindow` stops rounding the HWND mask, flushes radius when the window matches `avail`, and answers `WM_NCHITTEST` like Reader. Open-detail geometry (`expand_from_dock`) is unchanged.

**Tech Stack:** PySide6, Win32 `WM_NCHITTEST`, pytest-qt.

## Global Constraints

- Theme hex and 16px shell radius except when flush to the work area (then 0).
- `Qt.Tool | FramelessWindowHint`, tray, no 保存/关闭.
- Opening a card must not move the parked rail.
- `geometry_for_screen` remains first-launch collapsed right-third.

---

### Task 1: Radius and hit-test helpers

**Files:**
- Modify: `src/tasker/shell/window.py`
- Test: `tests/test_window.py`

**Interfaces:**
- Produces: `paper_corner_radius(geo: QRect, avail: QRect, slack: int = 2) -> int`
- Produces: `HTCLIENT`, `HTLEFT`, `HTRIGHT`, `HTTOP`, `HTTOPLEFT`, `HTTOPRIGHT`, `HTBOTTOM`, `HTBOTTOMLEFT`, `HTBOTTOMRIGHT`
- Produces: `hit_test_local(size: QSize, local: QPoint, margin: int = FRAME_MARGIN) -> int`

- [x] Write failing tests for radius and eight-way hit-test
- [x] Implement the helpers
- [x] Tests pass
- [x] Commit

### Task 2: Flush layout + native resize frame

**Files:**
- Modify: `src/tasker/shell/window.py`
- Modify: `src/tasker/theme.py` (`#shell[flush="true"]` radius 0)
- Modify: `docs/superpowers/specs/2026-09-15-ui-contract-lock.md` map
- Test: `tests/test_window.py`

**Interfaces:**
- Consumes: Task 1 helpers
- Produces: `DockWindow._apply_round_mask` uses radius 0 + `flush` + `clearMask` when filled; otherwise `round_window_mask` on the full window rect
- Produces: `DockWindow.nativeEvent` returns `hit_test_local` for `WM_NCHITTEST`

- [x] Write failing test: fill `avail` while expanded, rail width/right edge unchanged, detail stretches
- [x] Implement flush + clearMask + nativeEvent
- [x] Full `tests/test_window.py` plus suite
- [x] Freeze exe, desktop shortcut, STATUS, commit
