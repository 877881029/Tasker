# 紧急任务 DDL 倒计时（计划）

规格：`docs/superpowers/specs/2026-10-12-urgent-deadline-design.md`

- [x] 1. 测试先行：`format_countdown`、`Item.deadline` 读写往返、旧文件兼容、紧急组 DDL 排序。
- [x] 2. `store.py`：`deadline` 字段、front matter 读写、`set_deadline()`、排序。
- [x] 3. `deadline.py`：倒计时格式化、预设时间、DDL 菜单。
- [x] 4. 详情 DDL 胶囊 + 菜单；列表倒计时胶囊 + 30 秒刷新。
- [x] 5. 全量测试、截图验收、重打包部署、STATUS、推送。
