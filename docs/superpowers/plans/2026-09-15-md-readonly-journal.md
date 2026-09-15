# Markdown file store + read-only journal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist each task as `%LOCALAPPDATA%\Tasker\tasks\<id>.md` with YAML; open read-only; Ctrl+I prepends a new record; Ctrl+S saves to read-only; Esc saves and closes the bubble.

**Architecture:** `journal.py` dumps/parses stamped Markdown (not JSON). `Store` reads/writes those files under `tasks_dir()`; SQLite is only a one-shot migrator. `JournalPane` loads read-only; Ctrl+I prepends; autosave-on-keystroke is removed. Dock chrome drops 事项.

**Tech Stack:** PySide6, pytest / pytest-qt, stdlib YAML-subset (no PyYAML).

## Global Constraints

- Task files: `TASKER_DATA_DIR/tasks/<id>.md` (prod: `%LOCALAPPDATA%\Tasker\tasks\`).
- YAML keys: `title`, `state`, `resume_state`, `created_at`, `updated_at`.
- Do not rewrite image paths. Clipboard-only PNG may write `tasks/<id>/<uuid>.png`.
- Delete unlinks the `.md` only.
- No new `tasker.sqlite` on fresh installs.
- `Store(root: Path)` is the data root (tests pass `tmp_path`), not a sqlite path.

---

### Task 1: Journal Markdown (no hour merge)

**Files:**
- Modify: `src/tasker/journal.py`
- Modify: `tests/test_journal.py`

**Interfaces:**
- Produces: `stamp_for(when) -> str`, `parse_journal(body) -> list[tuple[str,str]]`, `dump_journal(entries) -> str`, `prepend_record(entries, when) -> list[tuple[str,str]]` (always prepends a new empty stamp, even same hour). Keep `parse_journal` able to read old JSON lists for migrate. Drop `ensure_current` from load path (may keep function unused or delete).

- [ ] **Step 1: Failing tests** in `tests/test_journal.py`

```python
def test_dump_separates_records_with_one_blank_line():
    blob = dump_journal([("260915.4PM", "新"), ("260915.3PM", "旧")])
    assert blob == "260915.4PM\n\n新\n\n260915.3PM\n\n旧"
    assert parse_journal(blob) == [("260915.4PM", "新"), ("260915.3PM", "旧")]

def test_prepend_record_same_hour_is_new_entry():
    when = datetime(2026, 9, 15, 15, 1)
    once = prepend_record([("260915.3PM", "已有")], when)
    twice = prepend_record(once, when)
    assert [e[0] for e in twice] == ["260915.3PM", "260915.3PM", "260915.3PM"]
    assert dump_journal(twice).count("260915.3PM") == 3
```

- [ ] **Step 2:** `.\.venv\Scripts\python.exe -m pytest tests/test_journal.py -q` — RED
- [ ] **Step 3:** Implement markdown dump/parse + `prepend_record`
- [ ] **Step 4:** Tests GREEN; keep JSON parse for `[{stamp,text},…]`
- [ ] **Step 5:** Commit

---

### Task 2: File Store + paths + migrate

**Files:**
- Modify: `src/tasker/paths.py` — add `tasks_dir() -> Path` (`data_dir() / "tasks"`). Keep `db_path()` for migrate-only. `attachments_dir(item_id)` becomes `tasks_dir() / item_id` (clipboard paste only).
- Modify: `src/tasker/store.py` — `Store(root: Path | None = None)` writes `<root>/tasks/<id>.md`.
- Modify: `src/tasker/app.py` — `Store(data_dir())`
- Modify: `tests/test_store.py`, `tests/test_paths.py` — `Store(tmp_path)`
- Create: `src/tasker/migrate.py` if sqlite import is easier isolated: `migrate_sqlite_if_needed(root: Path) -> None`

**Interfaces:**
- File body = YAML front matter + blank line + `dump_journal` body.
- `create` writes empty pending file. `delete` unlinks `.md` only.
- `write_paste_png` writes under `tasks/<id>/`.
- If `root/tasker.sqlite` exists and `tasks/` has no `*.md`, import rows then leave sqlite unused.

- [ ] **Step 1:** Tests: `test_create_writes_md_not_sqlite`, `test_save_roundtrip_yaml`, `test_delete_removes_md_not_foreign_image`, `test_migrate_sqlite_once`, `test_write_paste_png` parent is item id under tasks, `test_data_dir` tasks_dir
- [ ] **Step 2:** RED then implement
- [ ] **Step 3:** Update every `Store(tmp_path / "tasker.sqlite")` to `Store(tmp_path)`
- [ ] **Step 4:** `pytest tests/test_store.py tests/test_paths.py tests/test_journal.py -q` GREEN
- [ ] **Step 5:** Commit

---

### Task 3: Detail read-only, Ctrl+I / Ctrl+S / Esc, drop buttons

**Files:**
- Modify: `src/tasker/shell/detail.py`
- Modify: `tests/test_detail.py`, `tests/test_window.py` (remove save/close button asserts; Esc/close via shortcut)

**Interfaces:**
- `JournalPane.load`: parse only, all editors `setReadOnly(True)`, no `ensure_current`.
- `JournalPane.begin_write(when)`: `prepend_record`, rebuild, only head editable.
- Remove `eventFilter` that auto-opens current hour on printable keys.
- Disconnect autosave `journal.changed -> _save_body`.
- `DetailWindow`: Ctrl+I → begin_write; Ctrl+S → save_all then set all read-only; Esc → save_all + hide + closed; no 保存/关闭 widgets.
- Title / done / dot still save YAML immediately.

- [ ] **Step 1:** Tests as spec §7 (readonly until Ctrl+I; two Ctrl+I same hour; Ctrl+S file+readonly+visible; Esc hides; delete removes md; absolute image path unchanged)
- [ ] **Step 2:** RED / GREEN
- [ ] **Step 3:** Commit

---

### Task 4: Dock chrome (no 事项)

**Files:**
- Modify: `src/tasker/shell/window.py`
- Modify: `tests/test_window.py`

- [ ] **Step 1:** `test_dock_search_is_leftmost_without_brand` — no widget text 事项; search is first in chrome layout
- [ ] **Step 2:** Remove `_brand`; search still filtered by chrome drag (do not install drag filter on search)
- [ ] **Step 3:** Full `pytest -q` GREEN; commit; update `docs/STATUS.md`

---

## Spec coverage

| Spec | Task |
|---|---|
| File store YAML md | 2 |
| Read-only open / Ctrl+I new record / Ctrl+S / Esc | 3 |
| One blank line / same-hour new record | 1, 3 |
| Image paths unchanged; paste-only local png | 2, 3 |
| Delete md only | 2, 3 |
| Migrate sqlite once | 2 |
| No 事项, search fills left | 4 |
