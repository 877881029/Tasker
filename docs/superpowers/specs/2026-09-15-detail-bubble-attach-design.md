# Tasker 详情气泡贴在事项坞上

Date: 2026-09-15  
Status: Approved from user screenshots (two windows vs one attached bubble)  
Progress ledger: `docs/STATUS.md`

## 1. Goal

Opening a task must **not** spawn a second independent window. The detail pane is the left side of the **same** frameless paper shell as the right-hand task rail. Dragging the 事项 chrome moves the whole bubble; the detail’s offset from the rail stays fixed.

## 2. Layout

- Closed: dock is the right third of the available screen, list only.
- Open: shell expands to the available geometry. Left = detail, thin paper gap, right = chrome + cards (same third width as the collapsed dock).
- Selected card gets a cobalt edge so the bubble reads as coming from that task.
- Open shell uses a cobalt outline (`shell[bubble='true']`).

## 3. Windowing

- `DetailWindow` is a child of `detail_host` inside `DockWindow`. No `Qt.Tool` when parented.
- Close / Esc / delete hides the detail host and restores the right-third geometry.
- Pin still applies to the single dock window.

## 4. Out of scope

- Separate always-on-top for detail only.
- Pixel-perfect speech-bubble triangle (optional later; offscreen tests crash on custom `paintEvent`).
