# Detail expand, empty stamps, journal gap, Reader type

Date: 2026-09-17  
Status: Approved in chat  
Progress ledger: `docs/STATUS.md`

## Goal

Four user-confirmed polish items after the single-editor journal:

1. Clicking a card expands the detail **from the current dock geometry**. The rail’s right edge, x, y, and height stay put; the window grows left. Do not recompute a full-screen rect from a rail position that already shifted.
2. Ctrl+I may still open an empty new record for typing. If that record has **no new text** at save (Ctrl+S / Esc), drop it: no stamp on disk or in the editor afterward.
3. Adjacent records are separated by **one blank line** in the editor (not a large top-margin).
4. Journal body and timestamp gutter use Reader’s document family: Candara, then Calibri, then Segoe UI; normal weight. Do not mix Consolas with the body.
5. **Read-only** journal is the same Chromium path as Reader documents: `QWebEngineView` + `wrap_document_html` (Candara, 16px, line-height 1.72, `INK`). Stamps are one CSS grid column (`7.75rem`, right-aligned, nowrap); wrap stays in the body column. Ctrl+I still switches to `JournalEditor`. Do not render read-only journal with `QTextBrowser` (Qt HTML subset clips stamps and paints thinner/grayer type).
6. **Write** mode (`JournalEditor`) uses the same type scale: body Candara **16px** / line-height 1.72 / `INK`; gutter stamps **13px** weight 600. Do not inherit a 12pt stylesheet from `DetailWindow` onto the editor.

## Locked

Theme hex, `geometry_for_screen` right-third for the **collapsed** dock, Store/journal signatures, Ctrl+I still prepends while writing, Ctrl+S / Esc save behavior, tray, no 保存/关闭 buttons.
