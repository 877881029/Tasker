# Dock stays put; drag and resize the paper window

Date: 2026-09-17  
Status: Draft pending user review  
Progress ledger: `docs/STATUS.md`

## 1. Goal

Two user-confirmed polish items after the Chromium journal:

1. Clicking a card must **not move the rail** (the right-hand card column). After the user parks the dock, open-detail must not snap the shell back to the first-launch right-third, and must not stretch the window to the screen’s left edge.
2. The frameless paper window must be **draggable and resizable**. Header drag is effectively dead today because the search box stretches across the chrome; there is no resize frame.

## 2. What stays locked

Theme hex, 16px shell radius, tray, `Qt.Tool | FramelessWindowHint`, no 保存/关闭 buttons, Store/journal signatures, Ctrl+I / Ctrl+S / Esc, `geometry_for_screen` as the **first-launch collapsed** rect (right third). Geometry is remembered for the process lifetime only, not across restart.

## 3. Open / close geometry

One window. Detail is still embedded to the left of the rail.

- **Collapsed rail rect** `R = (x, y, w, h)` is the source of truth while the bubble is closed, and while it is open.
- **Open:** keep `R`’s screen pixels unchanged. Grow the window to the left by extra width `E`.  
  `window = (R.x - E, R.y, R.w + E, R.h)`.
- **First extra:** `E = 2 * R.w`. After the user resizes while expanded, remember `E = window.width - R.w` for the next open.
- **Clamp:** if `R.x - E < avail.x()`, shrink `E` so the left edge stays on this screen. Never move `R` to compensate. If `R` is already on the left edge, `E` can be 0: the journal column has no width until the user moves the window right or resizes.
- **Close:** set geometry back to `R` (current rail screen x/y, current rail width, current window height). Do not call `geometry_for_screen`.
- **After a move while expanded:** `R.x/y` follow the rail’s screen position so close lands where the rail now is.
- **`expand_from_dock(collapsed, extra_width, avail)`** replaces “fill to `avail.x()`”. Tests must prove the rail’s right edge, x, y, and height are unchanged.

Supersedes UI contract map “Expanded: full available geometry” and the old `expand_from_dock(..., avail)` that set `x = avail.x()`.

## 4. Drag

Empty paper moves the whole shell (rail + detail together):

- Chrome padding, empty list paper under/around cards, empty detail paper around the journal.
- **Not** search, `+` / pin / ×, cards, title, journal editor, WebEngine document, checkboxes, or other controls.

Prefer `QWindow.startSystemMove()` from those empty-paper presses so Windows snap still works. `ChromeBar` manual `move()` can remain only as a fallback if native move is unavailable.

## 5. Resize

Frameless 8-way resize: four edges and four corners, about 6–8px hit zone, including when a child sits under the edge (search near the top counts as a top-edge resize).

Prefer Windows hit-test / `QWindow.startSystemResize(edges)`. Minimum size: collapsed width ≥ 320 (existing contract), height tall enough for chrome + one card (~200px). While expanded, the rail width stays the last collapsed width; extra pixels go to the detail column. Dragging the **right** edge is a user resize, so the rail may move — that is allowed. Opening a card still must not move it.

## 6. Tests

- Move collapsed dock, `open_detail`: rail `mapToGlobal` top-left and size equal the parked rect; window grew left by ~`2 * rail.width` (or less if clamped).
- Clamp: parked at `avail.x()`, open does not change rail x; extra may be 0.
- Resize expanded, close, reopen: extra width matches the remembered value; rail still unmoved on that open.
- Close after move: collapsed geometry equals the rail’s new screen rect, not `geometry_for_screen`.
- Hit-test helper: points in the 8px frame are resize edges; points on empty list paper are move; points on search/card are neither.

## 7. Non-goals

- Persist position across process restart.
- Separate detail window.
- Changing first-launch right-third placement.
- Theme, tray, or journal editing.
