# 计划：窗口拖拽、缩放与屏幕自适应

规格：`docs/superpowers/specs/2026-10-10-window-drag-resize-screen-design.md`

- [ ] 1. 纯函数测试先行：`fit_into`、新 `expand_from_dock`（右移/最小详情）、`paper_action` 新拖拽名、`split_rail_width`。
- [ ] 2. 实现纯函数；`_screen()` 替换所有 `primaryScreen()`；屏幕信号 → `_fit_to_screen()`。
- [ ] 3. 展开/收起：程序摆放守卫、展开态最小宽度、收起回原位。
- [ ] 4. `CornerOverlay` 取代 `setMask`；双击最大化/还原。
- [ ] 5. 分隔线拖动调宽。
- [ ] 6. 全量测试、截图验收、重打包部署、STATUS、推送。
