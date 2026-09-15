# Paper Dock and Blank Draft Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** At most one untouched empty task, and a dock that looks like one paper sheet with sticky-note cards.

**Architecture:** Store owns blank-draft identity (`is_blank_draft`, `delete`, `collapse_blank_drafts`, `ensure_draft`). Dock `+` and startup call those APIs. Theme `dock_style()` paints paper chrome; pin uses `assets/icons/pin.svg`.

**Tech Stack:** PySide6, SQLite `Store`, pytest / pytest-qt, existing Tasker theme tokens.

## Global Constraints

- Python `>=3.12`, package `tasker`, tests use `TASKER_DATA_DIR`.
- Paper `#f4efe6`; no `background:white` on the dock shell.
- Blank draft = `pending` + empty title/status_pin/body_md.
- Pin is an icon, not the character 钉.
- Work on `main`; do not commit `dist/` or `build/`.

---

### Task 1: Blank-draft store lock

**Files:**
- Modify: `src/tasker/store.py`
- Test: `tests/test_store.py`

**Interfaces:**
- Consumes: existing `Store.create`, `list_visible`, `save`
- Produces: `is_blank_draft(item: Item) -> bool`, `Store.delete(item_id: str) -> None`, `Store.collapse_blank_drafts() -> Item | None`, `Store.ensure_draft() -> Item`

- [x] **Step 1: Write the failing test**
- [x] **Step 2: Run test to verify it fails**
- [x] **Step 3: Write minimal implementation** in `store.py`
- [x] **Step 4: Run test to verify it passes**
- [x] **Step 5: Commit** store lock

```python
from dataclasses import replace
from tasker.store import Store, is_blank_draft

def test_ensure_draft_reuses_and_collapses_blanks(tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path / "tasker.sqlite")
    a = store.create()
    b = store.create()
    titled = store.save(replace(store.create(), title="实事项"))
    urgent_empty = store.cycle_color(store.create().id)
    assert is_blank_draft(a) and is_blank_draft(b)
    assert not is_blank_draft(titled)
    assert not is_blank_draft(urgent_empty)
    kept = store.ensure_draft()
    ids = {i.id for i in store.list_visible()}
    assert kept.id in {a.id, b.id}
    assert titled.id in ids
    assert urgent_empty.id in ids
    blanks = [i for i in store.list_visible() if is_blank_draft(i)]
    assert len(blanks) == 1
    again = store.ensure_draft()
    assert again.id == kept.id
    store.save(replace(kept, title="已写"))
    created = store.ensure_draft()
    assert created.id != kept.id
```

- [x] **Step 2: Run test to verify it fails**

Run: `C:\Research\AgentDevelopor\Tasker\.venv\Scripts\python.exe -m pytest tests/test_store.py::test_ensure_draft_reuses_and_collapses_blanks -v`

Expected: FAIL (`is_blank_draft` not defined)

- [x] **Step 3: Write minimal implementation** in `store.py`

- [x] **Step 4: Run test to verify it passes**

- [x] **Step 5: Commit** store lock

### Task 2: Paper dock chrome, pin icon, `+` uses ensure_draft

**Files:**
- Create: `assets/icons/pin.svg`
- Modify: `src/tasker/theme.py` (`dock_style`)
- Modify: `src/tasker/shell/window.py`
- Test: `tests/test_window.py`, `tests/test_icon_assets.py`

**Interfaces:**
- Consumes: `Store.ensure_draft`, `Store.collapse_blank_drafts`, `dock_style()`
- Produces: `DockWindow._add` → `ensure_draft`; pin `QToolButton` with pin icon; list scroll objectName `listScroll`

- [x] **Step 1: Failing tests** for two `+` clicks, paper CSS, pin icon, `pin.svg` exists

- [x] **Step 2: Confirm fail**

- [x] **Step 3: Implement theme, pin svg, window**

- [x] **Step 4: Full `pytest tests/test_window.py tests/test_store.py tests/test_icon_assets.py -v` green

- [x] **Step 5: Commit**
