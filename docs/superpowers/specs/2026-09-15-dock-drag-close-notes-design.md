# Tasker 便签对齐、空列表与可拖动坞

Date: 2026-09-15  
Status: Approved from user screenshot + copy  
Progress ledger: `docs/STATUS.md`

## 1. Goal

The importance dot and title sit **in one sticky note**. An empty workbench shows **no ghost cards**. The dock can be **dragged** and closed with **X** after the pin.

## 2. Card layout

- `ItemCard` does not expand to fill the list (vertical size policy Maximum; list adds a stretch).
- Styled background is on so the note fill wraps **dot + title**.
- Dot is vertically centered with the title block, 20×20 solid circle, 8px gap.
- Title hover/focus does not draw a second large plate that splits from the dot; the note itself lights up.

## 3. Empty list

Blank drafts (`is_blank_draft`) stay in SQLite for `ensure_draft` reuse but **are not listed** unless the user just pressed `+` (`_active_draft_id`). Startup with leftover empty rows shows a blank paper, not placeholder titles.

## 4. Window chrome

- Frameless paper window; drag from the header (事项 label / header padding, not search or tool buttons).
- After pin: **X** (`closeDock`) closes the dock (and detail if open).
- Pin still toggles always-on-top and keeps frameless.
