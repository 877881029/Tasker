# Tasker 纸色坞与空白草稿单例

Date: 2026-09-15  
Status: Approved from user screenshot + copy (one blank draft; paper chrome; sticky-note cards; pin glyph)  
Progress ledger: `docs/STATUS.md`

## 1. Goal

The right-hand dock should feel like **one sheet of paper**. Tasks sit on it as **sticky notes**. Pressing `+` must not spawn a pile of untouched empty rows: there is **at most one blank draft** until the user actually adds content.

## 2. Blank-draft lock

A **blank draft** is an item that is still `pending`, with empty `title`, `status_pin`, and `body_md` (whitespace-only counts as empty). Cycling the color bar or checking done makes it a real item even with an empty title.

`Store.ensure_draft() -> Item`:

- If any blank drafts exist, **keep the newest** (`updated_at`), **delete the rest**, return the kept row.
- If none exist, `create()` as today.

Dock `+` calls `ensure_draft()` then focuses that card’s title. Opening the app also runs `collapse_blank_drafts()` so leftover empty rows from older builds collapse to one.

Search still filters the list; `+` during search still uses the same store rule (reuse/create blank), then refresh.

## 3. Paper chrome

Theme tokens stay Reader paper (`PAPER` `#f4efe6`, `CHROME` `#ebe4d8`, `INK`, `COBALT`, `LINE`). **No white fills** on the dock shell: window, list host, scroll viewport, search field, `+`, pin.

- **事项**: unchanged cobalt label.
- **查找**: keep placeholder, ink text, and a 1px `LINE` border; background **transparent**.
- **+**: keep the plus glyph; transparent, no white button plate; hover uses `CHROME`.
- **钉**: replace the 钉 character with a **pin icon** (`assets/icons/pin.svg`, cobalt stroke, transparent field). Checkable; no white plate.
- **List**: `QScrollArea` has **no frame**; viewport and list host are `PAPER` so there is no inner white well.
- **Cards**: sticky-note blocks (existing pending green / urgent red / done gray fills, radius, left color bar). Spacing between notes. Title field stays transparent on the note, not a white inner box.

Detail pane is already paper; this spec does not restyle Markdown `pre/code` `CARD` off-white inside the document view.

## 4. Testing

- Two `+` clicks with no title/body → one store row; title focused.
- After a non-empty title is saved, `+` creates a second row.
- Several leftover blank drafts → `collapse_blank_drafts` / `ensure_draft` leaves one.
- An urgent empty-title item is **not** treated as a blank draft.
- Dock stylesheet (and search/add/pin/list widgets) must not set `background:white`.
- Pin control text is empty; icon is non-null; `pin.svg` exists.
- Existing geometry, search, color, done, detail save/close tests stay green.

## 5. Non-goals

- New composer window separate from the list.
- Changing color-bar / checkbox semantics.
- Restyling the left detail Markdown chrome beyond current paper body.
