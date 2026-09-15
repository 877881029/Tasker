# Tasker 卡片只读、详情编辑

Date: 2026-09-15  
Status: Approved from user screenshot + copy  
Progress ledger: `docs/STATUS.md`

## 1. Goal

Dock notes are **read-only**. A click on the title (or the note) opens **detail**. Title, importance, done, body, and **delete** are edited only in detail.

## 2. Card

- Wrapping `QLabel` title, not a text editor.
- Importance dot is display-only.
- Click opens detail. `+` creates/reuses a draft and opens its detail.

## 3. Detail

- Title field, importance dot (cycles pending ↔ urgent), 完成, 保存, 关闭, **删除**.
- Delete removes the row, closes detail, refreshes the dock.
