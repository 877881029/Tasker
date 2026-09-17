# Journal as one continuous editor (timestamp gutter)

Date: 2026-09-17  
Status: Approved in chat (approach 1: single `QPlainTextEdit` + left timestamp extra area)  
Progress ledger: `docs/STATUS.md`

## 1. Goal

The detail journal is **one** wrapped editor that fills the reading pane, like Reader’s code view: a left gutter and a single scrollable text area. Open remains read-only. **Ctrl+I** still **prepends** a new stamped empty record and focuses it; after that the **entire** journal is editable, including older records and the new blank at the top. This removes per-record input boxes (the source of clipped “half lines”).

## 2. What stays locked

- Theme tokens, radii, cobalt T, tray, dock right-third, no 保存/关闭 buttons.
- Shortcuts: Ctrl+I begin write, Ctrl+S save and stay open read-only, Esc save and close.
- On-disk YAML + `dump_journal` / `parse_journal` (stamp line, then blank line, then body; newest first; same-hour Ctrl+I does not merge).
- `JournalPane` public methods: `load`, `collect`, `latest_status`, `begin_write`, `set_all_readonly`, `head_edit`.
- Header (dot, title, 完成, 删除) and `status_pin` = first non-empty text line of the newest record.

## 3. Layout

```
[ timestamp gutter ~118px ] [ one QPlainTextEdit, WidgetWidth wrap ]
```

- Gutter is a Reader-style extra area on the editor (`setViewportMargins`), not a column of `QLabel`s.
- Stamp is drawn **on the same row as the first visual line of that record**. Wrapped continuation lines have an empty gutter. Newest stamp `COBALT`, older `MUTED`. Gutter type: Consolas / Cascadia Mono, 13px, weight 600, right-aligned (same as today’s labels).
- The editor fills the detail body. **It** scrolls; there is no stack of per-record widgets and no `setFixedHeight` per entry.
- Gap between records remains about **two line heights**, via block top margin on every record after the first (not separate editors).

Empty new record: gutter shows the new stamp beside a one-line empty body in the **same** editor.

## 4. Document model

Stamps are **not** duplicated as visible text in the body. Each record’s stamp is metadata on that record’s first `QTextBlock`. The document text is only bodies. Ctrl+I inserts a new empty first record (new stamp metadata + empty body) above the rest; the previous first record keeps its stamp and gains the two-line top margin.

`collect()` walks records in document order and returns `dump_journal`. Only Ctrl+I (and load) create stamps. Typing, wrapping, and blank lines inside a record stay in that record. Merging or splitting records by editing is allowed only insofar as the user edits body text; they cannot create a new timestamp except via Ctrl+I.

`head_edit()` returns this single editor. After Ctrl+I the editor is not read-only; cursor at the start of the new empty record. `set_all_readonly()` locks that same editor.

Callers must not `setPlainText` the whole editor to fill only the newest record (that would wipe older text). Insert at the current cursor instead.

## 5. Contract delta

Supersedes `2026-09-15-md-readonly-journal-design.md` §2 “only that new record is editable” and §6 “Editing old records in place.”

Update `2026-09-15-ui-contract-lock.md` §3.1 / DetailWindow / JournalPane to:

- Ctrl+I prepends a new record **and** makes the **whole** journal editor writable.
- Journal UI is one editor + timestamp gutter, not one widget per record.

Do not change `tasker.journal` or `Store` signatures.

## 6. Non-goals

- Line numbers instead of timestamps.
- Putting stamp strings in the body (would duplicate the gutter).
- Ctrl+T visual Markdown preview.
- Theme, tray, geometry, or on-disk format changes.

## 7. Tests

- Open: single `QPlainTextEdit`, read-only, gutter shows each record’s stamp on its first line.
- Long wrapped body: last glyphs are inside the editor (no clip from `setFixedHeight`); editor height follows the pane, not the document.
- Ctrl+I: prepends empty stamped record, cursor at that empty body, **older text still present** and writable.
- Ctrl+I twice in the same hour: two records, `collect()` still `stamp\n\nnew\n\nstamp\n\nold`.
- After Ctrl+I, editing an older record is kept in `collect()`.
- Ctrl+S writes the `.md` and returns to read-only; Esc still saves and hides the bubble.
- Gap between two short records is about two line heights.
