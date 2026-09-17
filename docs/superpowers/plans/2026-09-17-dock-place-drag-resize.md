# Dock Place, Drag, Resize Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Opening a card leaves the parked rail still; the frameless paper window can be dragged from empty paper and resized from all eight edges.

**Architecture:** Pure helpers (`expand_from_dock`, `default_extra_width`, `edge_hit`, `paper_action`) own the math. `DockWindow` stores the rail rect `R` and remembered extra `E`, and uses native move/resize. One window, detail still embedded.

**Tech Stack:** PySide6, pytest / pytest-qt, existing `DockWindow` / `Store`.

## Global Constraints

- Theme hex and 16px shell radius stay locked.
- `geometry_for_screen` remains first-launch collapsed right-third.
- Tray, `Qt.Tool | FramelessWindowHint`, no 保存/关闭, Store/journal signatures, Ctrl+I / Ctrl+S / Esc stay locked.
- Geometry is session-only (not persisted across restart).
- Opening a card must not change rail screen x/y/width/height.
- First extra `E = 2 * R.w`, then remember last expanded extra; clamp to `avail.x()` without moving `R`.

---

### Task 1: expand_from_dock grows left by extra, never to screen origin

**Files:**
- Modify: `src/tasker/shell/window.py`
- Modify: `tests/test_window.py`

**Interfaces:**
- Produces: `expand_from_dock(collapsed: QRect, extra_width: int, avail: QRect) -> QRect`
- Produces: `default_extra_width(collapsed: QRect) -> int` (`collapsed.width() * 2`)

- [ ] **Step 1: Write the failing tests**

Replace `test_expand_from_dock_keeps_rail_right_edge` and add clamp + default extra tests:

```python
def test_expand_from_dock_grows_left_by_extra():
    avail = QRect(0, 0, 1920, 1080)
    collapsed = QRect(1000, 40, 400, 800)
    geo = expand_from_dock(collapsed, 800, avail)
    assert geo == QRect(200, 40, 1200, 800)
    assert geo.x() + geo.width() == collapsed.x() + collapsed.width()
    assert geo.y() == collapsed.y()
    assert geo.height() == collapsed.height()


def test_expand_from_dock_clamps_to_screen_left():
    avail = QRect(0, 0, 1920, 1080)
    collapsed = QRect(300, 80, 400, 700)
    geo = expand_from_dock(collapsed, 800, avail)
    assert geo == QRect(0, 80, 700, 700)


def test_expand_from_dock_zero_extra_when_on_left_edge():
    avail = QRect(0, 0, 1920, 1080)
    collapsed = QRect(0, 20, 400, 600)
    geo = expand_from_dock(collapsed, 800, avail)
    assert geo == collapsed


def test_default_extra_width_is_twice_rail():
    assert default_extra_width(QRect(100, 0, 400, 800)) == 800
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_window.py::test_expand_from_dock_grows_left_by_extra tests/test_window.py::test_expand_from_dock_clamps_to_screen_left tests/test_window.py::test_expand_from_dock_zero_extra_when_on_left_edge tests/test_window.py::test_default_extra_width_is_twice_rail -q --tb=short`

Expected: FAIL (TypeError extra_width / import default_extra_width)

- [ ] **Step 3: Write minimal implementation**

```python
def default_extra_width(collapsed: QRect) -> int:
    return max(0, collapsed.width() * 2)


def expand_from_dock(collapsed: QRect, extra_width: int, avail: QRect) -> QRect:
    extra = max(int(extra_width), 0)
    room = collapsed.x() - avail.x()
    extra = min(extra, max(room, 0))
    return QRect(
        collapsed.x() - extra,
        collapsed.y(),
        collapsed.width() + extra,
        collapsed.height(),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Same pytest command. Expected: PASS. Also run `tests/test_window.py` and fix `_place` call site so the suite still imports (`expand_from_dock(collapsed, extra, avail)`).

- [ ] **Step 5: Commit**

```bash
git add src/tasker/shell/window.py tests/test_window.py
git commit -m "Grow detail left by extra width so opening a card does not snap to the screen origin."
```

---

### Task 2: DockWindow open/close keeps the parked rail

**Files:**
- Modify: `src/tasker/shell/window.py` (`_place`, `open_detail`, `_on_detail_closed`)
- Modify: `tests/test_window.py`

**Interfaces:**
- Consumes: `expand_from_dock`, `default_extra_width`
- Produces: `DockWindow._collapsed_geo`, `DockWindow._extra_width` (`None` until first resize)

- [ ] **Step 1: Write the failing tests**

```python
def test_open_detail_does_not_move_parked_rail(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    from tasker.shell.window import DockWindow

    store = Store(tmp_path / "tasker.sqlite")
    item = store.save(replace(store.create(), title="停在这"))
    dock = DockWindow(store)
    qtbot.addWidget(dock)
    dock.show()
    parked = QRect(720, 120, 400, 640)
    dock.setGeometry(parked)
    qtbot.wait(20)
    dock.open_detail(item.id)
    qtbot.wait(20)
    rail_pos = dock.rail.mapToGlobal(QPoint(0, 0))
    assert rail_pos == parked.topLeft()
    assert dock.rail.width() == parked.width()
    assert dock.y() == parked.y()
    assert dock.height() == parked.height()
    assert dock.x() == parked.x() - parked.width() * 2
    assert dock.width() == parked.width() * 3
```

Keep `test_closing_detail_keeps_moved_dock_position` passing: after close, pos == parked and width == collapsed.

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_window.py::test_open_detail_does_not_move_parked_rail -q --tb=short`

Expected: FAIL because current `_place` sets `x = avail.x()`.

- [ ] **Step 3: Write minimal implementation**

On first open, `_extra_width = default_extra_width(collapsed)` if still `None`. `_place` when expanded:

```python
collapsed = self._collapsed_geo or QRect(self.geometry())
extra = self._extra_width if self._extra_width is not None else default_extra_width(collapsed)
self.rail.setFixedWidth(collapsed.width())
self.setGeometry(expand_from_dock(collapsed, extra, avail))
```

Do not call `geometry_for_screen` on later `_place()` unless `initial=True`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_window.py -q --tb=short`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tasker/shell/window.py tests/test_window.py docs/STATUS.md
git commit -m "Keep the parked rail still when a card opens the detail pane."
```

---

### Task 3: Remember extra width after the user resizes

**Files:**
- Modify: `src/tasker/shell/window.py`
- Modify: `tests/test_window.py`

**Interfaces:**
- Consumes: expanded `window.width - rail.width`
- Produces: `_extra_width` updated in `resizeEvent` while detail is visible; `_collapsed_geo` x/y follow the rail after move

- [ ] **Step 1: Write the failing test**

```python
def test_open_detail_reuses_resized_extra_width(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    from tasker.shell.window import DockWindow

    store = Store(tmp_path / "tasker.sqlite")
    item = store.save(replace(store.create(), title="记住宽"))
    dock = DockWindow(store)
    qtbot.addWidget(dock)
    dock.show()
    parked = QRect(900, 80, 360, 600)
    dock.setGeometry(parked)
    qtbot.wait(20)
    dock.open_detail(item.id)
    qtbot.wait(20)
    extra = 500
    dock.setGeometry(QRect(parked.x() - extra, parked.y(), parked.width() + extra, parked.height()))
    qtbot.wait(20)
    dock._detail.close_detail()
    qtbot.wait(20)
    dock.open_detail(item.id)
    qtbot.wait(20)
    assert dock.width() == parked.width() + extra
    assert dock.rail.mapToGlobal(QPoint(0, 0)) == parked.topLeft()
    assert dock.rail.width() == parked.width()
```

- [ ] **Step 2: Run test to verify it fails**

Expected: FAIL (second open uses `2 * rail` again).

- [ ] **Step 3: Write minimal implementation**

In `resizeEvent` / after geometry changes while expanded, set `_extra_width = max(0, self.width() - self.rail.width())` and refresh `_collapsed_geo` from the rail’s screen rect + window height.

On close, `setGeometry` to that rail rect.

- [ ] **Step 4: Run tests**

`.\.venv\Scripts\python.exe -m pytest tests/test_window.py -q --tb=short` PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "Remember the last expanded extra width so the next open matches the user's resize."
```

---

### Task 4: Empty-paper drag and eight-edge resize hit tests

**Files:**
- Modify: `src/tasker/shell/window.py`
- Modify: `tests/test_window.py`

**Interfaces:**
- Produces: `FRAME_MARGIN = 8`
- Produces: `edge_hit(pos: QPoint, size: QSize, margin: int = FRAME_MARGIN) -> Qt.Edges`
- Produces: `paper_action(pos: QPoint, size: QSize, object_name: str, margin: int = FRAME_MARGIN) -> str`  
  returns `"resize"`, `"move"`, or `"ignore"`
- Move names: `shell`, `dock`, `chrome`, `listHost`, `listScroll`, `detailHost`, `notch`
- Ignore names: `search`, `addBtn`, `pinBtn`, `closeDock`, `itemCard`, `titleField`, `journalEditor`, `journalDocument`, `doneBox`, `importance`, `deleteBtn`

- [ ] **Step 1: Write the failing tests**

```python
def test_edge_hit_eight_ways():
    size = QSize(400, 300)
    assert edge_hit(QPoint(2, 150), size) & Qt.Edge.LeftEdge
    assert edge_hit(QPoint(398, 150), size) & Qt.Edge.RightEdge
    assert edge_hit(QPoint(200, 2), size) & Qt.Edge.TopEdge
    assert edge_hit(QPoint(200, 298), size) & Qt.Edge.BottomEdge
    corners = edge_hit(QPoint(1, 1), size)
    assert corners & Qt.Edge.LeftEdge and corners & Qt.Edge.TopEdge
    assert not edge_hit(QPoint(200, 150), size)


def test_paper_action_move_resize_or_ignore():
    size = QSize(400, 300)
    assert paper_action(QPoint(2, 150), size, "search") == "resize"
    assert paper_action(QPoint(200, 150), size, "listHost") == "move"
    assert paper_action(QPoint(200, 150), size, "chrome") == "move"
    assert paper_action(QPoint(200, 150), size, "search") == "ignore"
    assert paper_action(QPoint(200, 150), size, "itemCard") == "ignore"
    assert paper_action(QPoint(200, 150), size, "journalDocument") == "ignore"
```

- [ ] **Step 2: Run tests to verify they fail**

Expected: FAIL import.

- [ ] **Step 3: Implement helpers and wire DockWindow**

Install an event filter on the dock. On left press:

- If `paper_action` is `resize` and `windowHandle()` exists, `startSystemResize(edges)`.
- If `move`, `startSystemMove()`, else fall back to existing `ChromeBar` move.
- Edge hits win even when the child is search.

Walk `childAt` parents for `objectName`. Set `minimumWidth(320)` and `minimumHeight(200)`.

- [ ] **Step 4: Run tests**

`.\.venv\Scripts\python.exe -m pytest tests/test_window.py tests/test_ui_contract.py -q --tb=short` PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "Let empty paper drag the shell and give the frameless window an eight-edge resize frame."
```

---

### Task 5: Contract note, full suite, freeze

**Files:**
- Modify: `docs/superpowers/specs/2026-09-15-ui-contract-lock.md` (expanded is no longer full available geometry; `expand_from_dock` grows left by extra)
- Modify: `docs/superpowers/specs/2026-09-17-dock-place-drag-resize-design.md` Status: Implemented
- Modify: `docs/STATUS.md`

- [ ] **Step 1:** Update contract map sentence: expanded = parked rail + extra to the left, not full screen.

- [ ] **Step 2:** `.\.venv\Scripts\python.exe -m pytest -q --tb=short` PASS

- [ ] **Step 3:** Kill `Tasker.exe`, run `scripts\build_windows.ps1`, refresh desktop shortcut with `overwrite=True`.

- [ ] **Step 4:** Commit STATUS + contract; try `git push origin main`.

---

## Spec coverage

| Spec | Task |
|---|---|
| Rail frozen on open | 1, 2 |
| Default extra 2× then remember | 1, 3 |
| Clamp without moving R | 1 |
| Close restores R | 2, 3 |
| Empty-paper drag | 4 |
| 8-way resize, 6–8px, including over search | 4 |
| First-launch right-third | unchanged `geometry_for_screen` |
| Freeze | 5 |
