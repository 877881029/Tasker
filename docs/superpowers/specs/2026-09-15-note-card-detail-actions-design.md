# Tasker 便签卡片与详情操作

Date: 2026-09-15  
Status: Approved from user screenshot + copy  
Progress ledger: `docs/STATUS.md`

## 1. Goal

Each dock card is only a **sticky note**: a solid importance dot and a taller wrapping title. Opening detail, marking done, and deleting happen in the **detail pane**, not as extra chrome on the card.

## 2. Card

- Left: **solid circle** (not a thin bar). Click cycles pending ↔ urgent. Done items show a gray circle and do not cycle (existing `cycle_color` rule).
  - pending fill `#22c55e`, urgent `#ef4444`, done `#9ca3af`. Circle 20×20, `border-radius: 10px`.
- Title: wrapping field, **minimum height 72px**, so two–three lines of title show on the dock.
- Hover / press on the title box: **light up** (chrome fill + cobalt border). Clicking the title **when it does not already have focus** opens detail. Newly created cards still receive focus so the first title can be typed on the card.
- No **详情** button. No done checkbox on the card. Gray card fill for done remains.

## 3. Detail

- **完成** checkbox in the header (same `set_done` semantics as before).
- **删除** removes the row (`Store.delete`), hides the pane, and refreshes the dock. Do not save after delete.
- 保存 / 关闭 unchanged.

## 4. Testing

- Card has no `openDetail` control and no done checkbox; importance control stylesheet includes `border-radius:10px`.
- Title `minimumHeight >= 72`; click unfocused title opens detail.
- Detail 完成 marks done and grays the card after refresh.
- Detail 删除 removes the store row and hides the pane.
- Existing search, blank-draft lock, pin, save/close stay green.
