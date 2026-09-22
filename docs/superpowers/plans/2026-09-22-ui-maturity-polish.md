# UI maturity polish implementation plan

> Execute task-by-task with tests first. Preserve the approved UI contract and the behavior boundaries in the accompanying spec.

**Goal:** Make Tasker's existing paper-workbench UI legible, keyboard-operable, and trustworthy without changing its task model, data, shortcuts, tray lifecycle, or window geometry.

**Architecture:** Add small native Qt presentation helpers and private widget state. `ItemCard` owns keyboard activation and accessible task text. `DockWindow.refresh` owns list empty states and dynamic tab order. `DetailWindow` owns journal status copy and the private delete-confirmation timer. Theme QSS provides focus treatment using existing tokens.

**Tech stack:** PySide6, Qt accessibility properties, QSS, pytest-qt.

## Global constraints

- No new public Store/Journal/shell methods or data fields.
- No new keyboard chords, buttons, dialogs, colors, animation, or window geometry.
- Existing object names remain unchanged.
- Tests precede implementation within each task.
- User-visible completion requires a frozen EXE rebuild and desktop shortcut refresh.

---

### Task 1: Journal workflow status

**Files:**
- Modify: `tests/test_detail.py`
- Modify: `src/tasker/shell/detail.py`
- Modify: `src/tasker/theme.py` only if a shared locked-token style is required

**Tests first:**
- Read/load state shows `Ctrl+I 写入 · Ctrl+S 保存 · Esc 收起`.
- `begin_write` shows `正在写入 · Ctrl+S 保存 · Esc 保存并收起`.
- `save_keep_open` shows `已保存 · Ctrl+I 继续写入 · Esc 收起`.
- Loading another task resets saved/write state.

**Implementation:**
- Add a non-interactive `QLabel` between the existing header and journal.
- Keep the label keyboard-neutral and accessible.
- Update only from `load`, `begin_write`, and `save_keep_open`.

- [ ] Failing tests
- [ ] Implementation
- [ ] Targeted tests pass
- [ ] Commit and push

### Task 2: Keyboard and accessibility

**Files:**
- Modify: `tests/test_window.py`
- Modify: `tests/test_detail.py`
- Modify: `src/tasker/shell/window.py`
- Modify: `src/tasker/shell/detail.py`
- Modify: `src/tasker/shell/journal_edit.py`
- Modify: `src/tasker/theme.py`

**Tests first:**
- Item card focus policy is keyboard reachable.
- Enter and Space activate the existing open callback.
- Card accessible name includes textual state and title.
- Add, pin, hide, state, journal, and destructive controls expose accessible names.
- Dynamic cards follow rail controls in deterministic tab order.
- QSS contains visible cobalt focus treatment for tools/cards.

**Implementation:**
- Add keyboard activation to `ItemCard`.
- Set accessible names/descriptions and state tooltips during `apply_item`.
- Set explicit rail control names and journal surface names.
- Wire tab order after every list refresh.
- Use existing cobalt token for focus; do not change selected/hover semantics.

- [ ] Failing tests
- [ ] Implementation
- [ ] Targeted tests pass
- [ ] Commit and push

### Task 3: Empty and lifecycle states

**Files:**
- Modify: `tests/test_window.py`
- Modify: `src/tasker/shell/window.py`
- Modify: `src/tasker/theme.py`

**Tests first:**
- Empty store shows `还没有事项` / `点 + 开始记录`.
- Empty search shows `没有找到匹配事项` / `换个关键词试试`.
- Empty message disappears when a task matches.
- Empty labels are not focusable and do not change Store contents.
- Shell × tooltip is `隐藏到托盘`.

**Implementation:**
- Add one two-line empty-state label through `DockWindow.refresh`.
- Derive copy only from `query` and result count.
- Keep copy in the normal list layout with no click handling or new object model.

- [ ] Failing tests
- [ ] Implementation
- [ ] Targeted tests pass
- [ ] Commit and push

### Task 4: Inline safe deletion

**Files:**
- Modify: `tests/test_detail.py`
- Modify: `tests/test_window.py`
- Modify: `src/tasker/shell/detail.py`

**Tests first:**
- First click changes copy to `确认删除` and preserves the item.
- Second armed click removes the item through the existing Store path.
- Loading a task resets confirmation to `删除`.
- Timer expiry resets confirmation without deleting.
- Existing detail close and save behavior remains unchanged.

**Implementation:**
- Keep `delete_item` as the slot but make it a two-step private state machine.
- Use a single-shot four-second `QTimer`.
- Style default and armed states only with locked theme tokens.
- Stop/reset the timer on `load` and successful deletion.

- [ ] Failing tests
- [ ] Implementation
- [ ] Targeted tests pass
- [ ] Commit and push

### Task 5: Integrated verification and release

**Files:**
- Modify: `docs/STATUS.md`
- Modify: `docs/superpowers/plans/2026-09-22-ui-maturity-polish.md`
- Rebuild: `dist/Tasker/Tasker.exe`
- Refresh: desktop `Tasker.lnk`

**Verification:**
- Run focused detail/window tests.
- Run complete test suite with the repository `src` import path.
- Perform one bounded native visual pass: collapsed rail, expanded detail, write mode, delete confirmation, no-results state, keyboard focus.
- Confirm no theme token, public interface, geometry, or shortcut drift.
- Run the Impeccable native critique checklist once; do not run the web detector again.
- Stop any running `Tasker.exe`, run `scripts/build_windows.ps1`, and overwrite the desktop shortcut.

- [ ] Targeted tests pass
- [ ] Full suite passes
- [ ] Native visual pass passes
- [ ] Frozen EXE rebuilt
- [ ] Desktop shortcut refreshed
- [ ] STATUS marked complete
- [ ] Final commit and push
