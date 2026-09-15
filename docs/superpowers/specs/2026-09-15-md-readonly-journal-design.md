# Tasker Markdown files, read-only open, Ctrl+I records

Date: 2026-09-15  
Status: Approved in chat (YAML md under LocalAppData; Reader shortcuts; no SQLite going forward)  
Progress ledger: `docs/STATUS.md`

## 1. Goal

Stop storing tasks in SQLite. Each task is one Markdown file under `%LOCALAPPDATA%\Tasker\tasks\` (or `TASKER_DATA_DIR/tasks` in tests). Opening a task is **read-only**. Writing uses Reader’s keys: **Ctrl+I** starts a **new** journal record, **Ctrl+S** saves and returns to read-only (bubble stays), **Esc** saves and **closes** the detail bubble. Dock chrome drops the 事项 label; search fills the left side.

## 2. Shortcuts and chrome

- Open detail: journal records are read-only; the user cannot type in existing or empty body until Ctrl+I. The header title, importance, and done stay usable (they write YAML, not a new record).
- Ctrl+I: prepend a **new** record even if the top stamp is the same hour. Only that new record is editable.
- Ctrl+S: write the `.md` to disk, then read-only again. Detail stays open.
- Esc: save (same write as Ctrl+S) then hide the detail host and shrink the dock (replaces Close).
- Remove **保存** and **关闭**. Keep **删除**, title, importance dot, and done.
- Dock header: no 事项 label. Search is the left-most control and stretches.

## 3. File format

Path: `tasks/<stable-id>.md`. Renaming the title does **not** rename the file.

```markdown
---
title: 改脚本
state: pending
---

260915.4PM

Newer record text, links, images

260915.3PM

Older record
```

- `state`: `pending` | `urgent` | `done`. Dot cycle and done checkbox update YAML and write the file.
- Records are newest-first. Adjacent records are separated by **exactly one blank line**.
- The stamp is the first line of the record (`YYMMDD.hAM/PM`), not merged with same-hour siblings.
- `status_pin` for empty/search helpers is the first non-empty text line of the newest record (not the stamp).

## 4. Images and links

- Markdown image and hyperlink syntax stays in the file as the user wrote it.
- **Do not copy, move, or rewrite** existing image paths when reading or migrating. Preview loads the path in the file.
- Clipboard paste with **no** source path may write a file next to the task (`tasks/<id>/…`) and insert that relative link. That is the only case Tasker creates an image file.
- Delete task: delete the `.md` only. Do **not** delete images that live outside Tasker, including original user folders.

## 5. Store

- Replace SQLite `Store` with a file store that lists `tasks/*.md` with YAML front matter.
- Create: new uuid filename, empty title, `state: pending`, empty body.
- Save: overwrite that file. Delete: unlink the `.md`.
- `ensure_draft` / collapse blanks: at most one empty pending file (no title, no record text).
- Search: filter on title + full markdown body.
- No new `tasker.sqlite`. If `tasker.sqlite` exists and `tasks/` has no task files, **one-shot migrate** JSON/legacy bodies into the format above, keeping image paths unchanged; then stop using the db.

## 6. Non-goals

- Editing old records in place.
- Ctrl+T preview toggle (Reader markdown visual stack).
- Deleting the user’s original image files.
- Storing tasks next to the frozen exe.

## 7. Tests

- Open is read-only (head editor not editable until Ctrl+I).
- Ctrl+I twice in the same hour yields two records with a blank line between.
- Ctrl+S writes the `.md` and returns to read-only; detail still visible.
- Esc writes then hides the bubble.
- Delete removes the `.md`; sqlite is not created for new installs.
- Chrome has no 事项; search is present and expanding.
- Image markdown with an absolute path is left unchanged on save.
