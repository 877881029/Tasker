# Fill the work area; keep 8-way resize

Date: 2026-09-21  
Status: Approved in chat (user chose A, then “可以，开始吧”)  
Progress ledger: `docs/STATUS.md`

## Goal

Tasker’s paper window should follow the window like Reader’s document surface: **edges and corners resize freely**, and the shell **may occupy the whole work area**. The rail stays on the right; leftover width and height go to the detail column. Do **not** use OS maximize (that typically locks the size until restore).

## What stays locked

Theme hex, tray, `Qt.Tool | FramelessWindowHint`, no 保存/关闭, Store/journal signatures, Ctrl+I / Ctrl+S / Esc, `geometry_for_screen` first-launch collapsed right-third, opening a card still must **not** snap the parked rail.

## Behavior

1. **Open detail:** same as today — rail screen rect `R` unchanged; window grows left by extra `E` (`2 × R.w` first, then remembered). `expand_from_dock` still clamps that *open* extra so the window does not jump past `avail`.
2. **After that, user resize is free:** eight edges/corners, including over the search box on the frame. The user may pull the window until it matches `availableGeometry()`. Shrinking from a filled window is allowed immediately (no restore step).
3. **Layout:** while detail is open, rail width stays the last collapsed width; extra pixels go to `detailHost` (stretch). Height of rail and detail follow the shell.
4. **Filled work area:** if the window rect is within 2px of `avail` on x, y, width, and height, treat it as flush: shell corner radius **0** and no rounded mask so the paper meets the work-area edges. Otherwise keep **16px** and clip the HWND with a rounded mask on the **full** window rect (do not shrink by 1px — that misaligns the four corners). `WM_NCHITTEST` still uses the 8px frame.
5. **Hit-testing:** Windows `WM_NCHITTEST` on an 8px frame (Reader’s pattern), so resize does not depend on a child eating the press. Empty paper still `startSystemMove()`. Interactive controls stay client hits except on the frame.

## Tests

- `paper_corner_radius(geo, avail)` is 16 when inset, 0 when `geo` matches `avail`.
- Expanded window set to `avail`: rail width unchanged, rail right edge still `R`’s right edge, `detailHost` width ≈ `avail.width - rail.width` (notch included in the leftover).
- `hit_test_local` maps the 8px frame to the eight Win32 edge codes; interior is `HTCLIENT`.
- Existing open-detail / clamp / remembered extra tests still pass.

## Non-goals

- A maximize chrome button.
- Persist geometry across process restart.
- Changing first-launch right-third placement.
- Theme hex, tray, journal editing.
