# Tasker 圆点齐顶、圆角坞与单实例

Date: 2026-09-15  
Status: Approved from user screenshot + copy  
Progress ledger: `docs/STATUS.md`

## 1. Goal

Keep the current sticky-note look. Move the importance dot to the **top-left, same row as the title**. Round the **outer dock**. Only **one process/window**. Collapse leftover empty example notes to **one**.

## 2. Note

- Dot `AlignTop` with the title field (not vertically centered in the tall card).
- Empty notes (no title, status pin, or body, any state) collapse to a single row on launch; extras are deleted.

## 3. Outer chrome

- Frameless dock uses a 16px rounded paper shell and a 1px `LINE` border.
- Windows DWM rounded corners when available.

## 4. Single instance

- `QLockFile` + `QLocalServer` name `Tasker.SingleInstance.v1`.
- A second desktop click activates the existing dock (show/raise) and exits.
- Tests use `TASKER_IPC_NAMESPACE`.
