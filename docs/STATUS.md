# Tasker 项目状态（AI 接手必读）

最后更新：2026-09-15  
Git：`main` 应与 `origin/main` 同步（https://github.com/877881029/Tasker ）。

## 当前目标

**任务改为 LocalAppData 下的 Markdown 文件；详情默认只读（Ctrl+I / Ctrl+S / Esc）**（规格已批准，计划已写，开始实现）

规格：`docs/superpowers/specs/2026-09-15-md-readonly-journal-design.md`  
计划：`docs/superpowers/plans/2026-09-15-md-readonly-journal.md`

## 下一步

按计划 TDD：journal md → file store → 详情快捷键 → 坞顶栏

## 上一目标（已完成）

**详情贴在事项坞上，拖顶栏时一起移动**（冻结包已重建）

## 背景

Tasker 是 Windows 桌面个人工作台。数据 `%LOCALAPPDATA%\Tasker\`。远程 https://github.com/877881029/Tasker

## 已完成

- v1、冻结、纸色坞、单实例、卡片只读详情编辑
- 2026-09-15：详情倒序时间日志；详情嵌进坞
- 规格：md 文件存储 + Reader 快捷键（待实现）

## 阻塞项

- 无
