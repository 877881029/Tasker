# Tasker UI maturity polish

Date: 2026-09-22  
Status: Approved in chat  
Method: Impeccable `init -> document -> critique -> polish`  
Progress ledger: `docs/STATUS.md`

## Goal

Improve Tasker's operational clarity and accessibility without changing its core task model, Markdown data, public interfaces, locked theme, keyboard chords, tray lifecycle, or window geometry.

The interface remains the same “桌边工作纸”: warm, restrained, flat, and beside the user's work. This pass makes the paper more legible and trustworthy rather than adding dashboard chrome.

## Evidence

The Impeccable dual-agent critique scored the current native surface 15/40 on Nielsen heuristics. Visual identity is strong; the main maturity gaps are silent system state, shortcut recall, mouse-only cards, color-only task state, indistinguishable empty states, and irreversible deletion.

GitHub comparison found the closest references to be:

- QOwnNotes: tray-first, low-friction local Markdown capture.
- Sleek: deliberately narrow plain-text task UI.
- Super Productivity: keyboard edge-case polish and local recovery confidence.

The references inform maturity patterns only. Tasker does not adopt their account, sync, hierarchy, plugin, or dashboard features.

## Locked constraints

- Preserve all values and public names in `src/tasker/theme.py`.
- Preserve `Store`, journal, paths, IPC, shell, and shortcut interfaces from the UI contract.
- Preserve task states, ordering, Markdown schema, and stable task filenames.
- Preserve `Ctrl+I`, `Ctrl+S`, and `Esc`; do not add or replace keyboard chords.
- Preserve tray behavior, single instance, `Qt.Tool | FramelessWindowHint`, rail placement, expansion, dragging, eight-way resize, and flush-work-area radius behavior.
- Preserve the detail header's existing controls. No visible Save or Close button.
- No shadows, gradients, glass, animation, new palette, dashboard panels, project hierarchy, account, cloud, or collaboration UI.

## Behavior

### 1. Journal workflow guidance and status

- Add one compact, non-interactive status line between the detail header and journal.
- Read state: `Ctrl+I 写入 · Ctrl+S 保存 · Esc 收起`.
- Write state: `正在写入 · Ctrl+S 保存 · Esc 保存并收起`.
- After Ctrl+S: `已保存 · Ctrl+I 继续写入 · Esc 收起`.
- Loading another task resets the line to the read-state guidance.
- The line uses the existing paper/ink/cobalt vocabulary, adds no new button, and does not change save behavior.

### 2. Keyboard and assistive operation

- Every task card accepts keyboard focus.
- Enter and Space open the focused card through the existing `open_detail` callback.
- A focused card receives the existing cobalt 2px treatment.
- Cards expose an accessible name containing textual task state and title, plus a description explaining Enter/Space.
- Add, pin, hide, task-state, title, journal, completion, and delete controls receive explicit accessible names where visible text is insufficient.
- Dynamic card creation establishes a deterministic tab order after the four rail controls.
- Task state remains visually colored, but is also present in tooltip/accessibility text.

### 3. Safe inline deletion

- First activation of `删除` does not delete. It changes the same button to `确认删除`.
- The confirmation state uses only existing urgent/background/line/ink tokens.
- A second activation while armed calls the existing `Store.delete` path and closes detail.
- The confirmation automatically resets after four seconds.
- Loading another task or completing deletion clears the confirmation state.
- No modal, new public API, undo system, or new data shape is introduced.

### 4. Empty and lifecycle states

- An empty rail shows `还没有事项` and `点 + 开始记录`.
- A search with no matches shows `没有找到匹配事项` and `换个关键词试试`.
- Empty-state text is non-interactive, keyboard-neutral, and uses existing tokens.
- The shell × tooltip becomes `隐藏到托盘`; its behavior remains hide-only.
- Empty states must not create Store items or alter search behavior.

### 5. Internal layout polish

- Keep the outer expanded geometry, rail width, notch, and detail stretch unchanged.
- Tighten header-to-status-to-journal grouping so the status belongs to the journal workflow.
- Keep journal body measure and timestamp gutter behavior unchanged; do not cap the detail width or introduce a nested card.
- Use spacing and focus treatment, not new separators or decoration, to clarify hierarchy.

## Tests

- Focused card opens with Enter and Space.
- Card accessible name includes textual state and title.
- Rail tools have explicit accessible names; × tooltip says `隐藏到托盘`.
- No-task and no-search-result messages are distinct and disappear when results exist.
- `begin_write`, `save_keep_open`, and `load` set the required status text.
- First delete click arms confirmation without deleting; second deletes; load/reset disarms it.
- Existing Store, detail save, geometry, theme, journal, tray, and packaging tests remain unchanged and pass.

## Non-goals

- Changing first-open or filled-work-area geometry.
- Adding global shortcuts, synchronization, tags, projects, reminders, timers, undo history, or backups.
- Replacing Chromium read rendering or the existing `JournalEditor` write path.
- Changing locked color values to solve the known small-muted-text contrast limitation.
