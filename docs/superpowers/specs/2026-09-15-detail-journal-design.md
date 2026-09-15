# Tasker 详情时间日志

Date: 2026-09-15  
Status: Approved from user screenshots + copy  
Progress ledger: `docs/STATUS.md`

## 1. Goal

Keep the detail header (dot, title, actions) and replace Markdown / 最新状态 with a **reverse-chronological journal**. The left gutter is a time stamp `YYMMDD.hAM/PM` (example `260915.3PM`), not line numbers. Typing always lands on the current hour’s block at the **top**.

## 2. Journal

- Entries stored as JSON in `body_md`. Legacy Markdown becomes one untitled block.
- `ensure_current` prepends a block for this hour if the top stamp is stale.
- `status_pin` is the first line of the newest block (for search/empty checks).
- Header controls use a larger type and a 32px importance dot.
