# Journal single editor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace per-record journal boxes with one wrapped `QPlainTextEdit` plus a left timestamp gutter so the whole note is one scrollable editor.

**Architecture:** New `JournalEditor` (Reader-style extra-area gutter) owns document bodies and stamp metadata on each record’s first `QTextBlock`. `JournalPane` hosts that single editor. `collect()` still returns `dump_journal`. Ctrl+I prepends an empty stamped record and unlocks the whole editor.

**Tech Stack:** PySide6, pytest / pytest-qt, existing `tasker.journal` / `Store`.

## Global Constraints

- Do not change theme token names or hex, radii, tray, dock right-third, or 保存/关闭 buttons.
- Shortcuts stay: Ctrl+I begin write, Ctrl+S save and stay open read-only, Esc save and close.
- Do not change `tasker.journal` or `Store` public signatures or on-disk YAML + stamp format.
- `JournalPane` public methods stay: `load`, `collect`, `latest_status`, `begin_write`, `set_all_readonly`, `head_edit`.
- Stamps are gutter-only, not duplicated in the body text.
- Gutter width 118px; newest stamp `COBALT`, older `MUTED`; Consolas/Cascadia Mono 13px weight 600, right-aligned.
- Record gap ≈ two line heights via block top margin on every record after the first.
- After Ctrl+I the **entire** editor is writable. Callers insert at the cursor; they must not `setPlainText` the whole editor to fill only the newest record.
- User-visible finish: rebuild `dist\Tasker\Tasker.exe` and overwrite desktop `Tasker.lnk`.

---

### Task 1: JournalEditor + pane (single editor, gutter, Ctrl+I whole-doc write)

**Files:**
- Create: `src/tasker/shell/journal_edit.py`
- Modify: `src/tasker/shell/detail.py` (`JournalPane` only; `DetailWindow` shortcuts unchanged)
- Modify: `tests/test_detail.py`
- Modify: `tests/test_window.py` (`head_edit().setPlainText` → `textCursor().insertText`)
- Modify: `docs/superpowers/specs/2026-09-15-ui-contract-lock.md` §3.1 Ctrl+I sentence and JournalPane bullet
- Modify: `docs/STATUS.md`

**Interfaces:**
- Consumes: `dump_journal`, `parse_journal`, `prepend_record`, theme `PAPER` `INK` `COBALT` `MUTED`
- Produces:
  - `class StampData(QTextBlockUserData)` with `.stamp: str`
  - `class JournalEditor(QPlainTextEdit)`:
    - `GUTTER_WIDTH = 118`
    - `load_entries(entries: list[tuple[str, str]]) -> None`
    - `entries() -> list[tuple[str, str]]`
    - `gutter() -> QWidget`
  - `JournalPane.head_edit() -> JournalEditor` (still a `QPlainTextEdit`)
  - `JournalPane.begin_write(when=None)` prepends then `setReadOnly(False)` on the one editor

- [ ] **Step 1: Write the failing tests** in `tests/test_detail.py` (replace journal-widget assertions)

```python
def _insert_head(win, text: str) -> None:
    cursor = win.journal.head_edit().textCursor()
    cursor.insertText(text)
    win.journal.head_edit().setTextCursor(cursor)


def test_open_is_readonly_until_ctrl_i(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path)
    item = store.save(replace(store.create(), body_md="260915.3PM\n\n旧记录"))
    win = DetailWindow(store)
    qtbot.addWidget(win)
    win.load(item)
    editors = win.journal.findChildren(QPlainTextEdit)
    assert len(editors) == 1
    assert win.journal.head_edit().isReadOnly()
    win.begin_write()
    assert not win.journal.head_edit().isReadOnly()
    assert win.journal.head_edit().entries()[1][1] == "旧记录"


def test_ctrl_i_same_hour_two_records(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path)
    item = store.create()
    win = DetailWindow(store)
    qtbot.addWidget(win)
    win.load(item)
    when = datetime(2026, 9, 15, 15, 1)
    win.journal.begin_write(when)
    _insert_head(win, "第一条")
    win.journal.begin_write(when)
    _insert_head(win, "第二条")
    assert [stamp for stamp, _text in win.journal.head_edit().entries()] == [
        "260915.3PM",
        "260915.3PM",
    ]
    blob = win.journal.collect()
    assert blob == "260915.3PM\n\n第二条\n\n260915.3PM\n\n第一条"


def test_ctrl_i_can_edit_older_record(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path)
    item = store.save(replace(store.create(), body_md="260915.3PM\n\n旧记录"))
    win = DetailWindow(store)
    qtbot.addWidget(win)
    win.load(item)
    when = datetime(2026, 9, 15, 16, 0)
    win.journal.begin_write(when)
    _insert_head(win, "新记录")
    blocks = []
    block = win.journal.head_edit().document().begin()
    while block.isValid():
        blocks.append(block)
        block = block.next()
    older = [b for b in blocks if b.text() == "旧记录"][0]
    cursor = win.journal.head_edit().textCursor()
    cursor.setPosition(older.position())
    cursor.movePosition(cursor.MoveOperation.EndOfBlock)
    cursor.insertText("已改")
    blob = win.journal.collect()
    assert "新记录" in blob
    assert "旧记录已改" in blob


def test_journal_gap_is_about_two_line_heights(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path)
    item = store.save(
        replace(
            store.create(),
            body_md="260916.11AM\n\n上一条短记录\n\n260916.10AM\n\n下一条短记录",
        )
    )
    win = DetailWindow(store)
    qtbot.addWidget(win)
    win.resize(720, 640)
    win.show()
    win.load(item)
    qtbot.wait(30)
    edit = win.journal.head_edit()
    line = edit.fontMetrics().lineSpacing()
    second = None
    block = edit.document().begin()
    seen = 0
    while block.isValid():
        data = block.userData()
        if data is not None and getattr(data, "stamp", ""):
            seen += 1
            if seen == 2:
                second = block
                break
        block = block.next()
    assert second is not None
    margin = second.blockFormat().topMargin()
    assert line * 1.5 <= margin <= line * 2.5


def test_journal_is_one_scrolling_editor(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path)
    body = (
        "260916.11AM\n\n"
        "这份文档有一个小优化应该是, 我们应该重点强调一下, 之前已经有了的skill不会在最新的部署脚本中覆盖"
        " 同时如果不是最新脚本来部署的, 那么其使用时也就不会被dashboard中检测到"
    )
    item = store.save(replace(store.create(), body_md=body))
    win = DetailWindow(store)
    qtbot.addWidget(win)
    win.resize(640, 480)
    win.show()
    win.load(item)
    qtbot.wait(80)
    edit = win.journal.head_edit()
    assert len(win.journal.findChildren(QPlainTextEdit)) == 1
    assert edit.gutter().width() == 118
    assert edit.height() == win.journal.height()
    assert edit.maximumHeight() > 10000 or edit.maximumHeight() == 16777215


def test_ctrl_s_writes_and_stays_readonly(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path)
    item = store.create()
    win = DetailWindow(store)
    qtbot.addWidget(win)
    win.show()
    win.load(item)
    win.begin_write()
    _insert_head(win, "已接到 setup")
    win.title_edit.setText("改脚本")
    win.save_keep_open()
    loaded = store.get(item.id)
    assert loaded is not None
    assert loaded.status_pin == "已接到 setup"
    assert loaded.title == "改脚本"
    assert win.journal.head_edit().isReadOnly()
    assert win.isVisible()
```

Also change `tests/test_window.py` `test_detail_save_and_close`:

```python
    dock._detail.begin_write()
    cursor = dock._detail.journal.head_edit().textCursor()
    cursor.insertText("正文")
    dock._detail.journal.head_edit().setTextCursor(cursor)
    dock._detail.save_keep_open()
```

Keep `test_detail_geometry_fills_left`, markdown/paste, image path, cycle/delete tests as they are.

- [ ] **Step 2: Run tests to verify they fail**

```
.\.venv\Scripts\python.exe -m pytest tests/test_detail.py::test_open_is_readonly_until_ctrl_i tests/test_detail.py::test_ctrl_i_can_edit_older_record tests/test_detail.py::test_journal_is_one_scrolling_editor -q --tb=short
```

Expected: FAIL (`entries` / `gutter` missing, or `len(editors) != 1`, or `_rows` still used).

- [ ] **Step 3: Write `journal_edit.py` and slim `JournalPane`**

`JournalEditor` copies Reader `CodeEditor` extra-area wiring (`blockCountChanged`, `updateRequest`, `resizeEvent`, `setViewportMargins`) but:

- gutter width is always 118
- background `PAPER`, no chrome divider
- paint stamp from `StampData` on that block only; first stamped block `COBALT`, later `MUTED`
- `AlignRight | AlignTop`
- `setLineWrapMode(WidgetWidth)`
- `setSizePolicy(Expanding, Expanding)` — never `setFixedHeight`
- `load_entries` rebuilds blocks: first block of each record gets `StampData(stamp)`; records after the first get `QTextBlockFormat.setTopMargin(2 * lineSpacing)`
- `entries()` walks blocks: a `StampData` starts a record; following unmarked blocks belong to it until the next stamp

`JournalPane`: one `JournalEditor` in a zero-margin layout (no `QScrollArea`, no `_rows`, no `_fit_editor`).

```python
def load(self, body: str, when: datetime | None = None) -> None:
    self.editor.load_entries(parse_journal(body))
    self.editor.setReadOnly(True)

def collect(self) -> str:
    return dump_journal(self.editor.entries())

def begin_write(self, when: datetime | None = None) -> None:
    moment = when or datetime.now()
    self.editor.load_entries(prepend_record(self.editor.entries(), moment))
    self.editor.setReadOnly(False)
    self.editor.setFocus()
    cursor = self.editor.textCursor()
    cursor.movePosition(cursor.MoveOperation.Start)
    self.editor.setTextCursor(cursor)

def set_all_readonly(self) -> None:
    self.editor.setReadOnly(True)

def head_edit(self) -> QPlainTextEdit:
    return self.editor
```

- [ ] **Step 4: Run tests GREEN**

```
.\.venv\Scripts\python.exe -m pytest tests/test_detail.py tests/test_window.py -q --tb=short
```

Expected: PASS. Then full `.\.venv\Scripts\python.exe -m pytest -q`.

- [ ] **Step 5: Patch the UI contract**

In `docs/superpowers/specs/2026-09-15-ui-contract-lock.md`:

- §3.1: `Ctrl+I` always **prepends** a new record (same hour ≠ merge) **and makes the whole journal editor writable**.
- DetailWindow bullet: `Ctrl+I` → `begin_write` (prepend + whole editor writable).
- JournalPane: one editor + timestamp gutter; public methods unchanged.

- [ ] **Step 6: Commit, freeze, STATUS**

```
git add src/tasker/shell/journal_edit.py src/tasker/shell/detail.py tests/test_detail.py tests/test_window.py docs/superpowers/specs/2026-09-15-ui-contract-lock.md docs/STATUS.md
git commit -m "Use one journal editor so wrapped notes are not clipped by per-record boxes."
```

Stop running `Tasker.exe`. Run `scripts\build_windows.ps1`. Overwrite desktop shortcut to `dist\Tasker\Tasker.exe`. STATUS: current goal complete; next step = double-click desktop Tasker and edit an old record after Ctrl+I.

---

## Spec coverage

| Spec | Task |
|---|---|
| One editor + extra-area gutter, stamps on first visual line | Task 1 |
| Open read-only; Ctrl+I prepend + whole doc writable | Task 1 |
| collect/dump_journal unchanged | Task 1 |
| Two-line gap via block margin | Task 1 |
| No setFixedHeight / no half-line clip | Task 1 |
| Contract delta | Task 1 Step 5 |
| Freeze + desktop lnk | Task 1 Step 6 |
