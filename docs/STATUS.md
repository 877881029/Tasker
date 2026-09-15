# Tasker 项目状态（AI 接手必读）

最后更新：2026-09-15  
Git：`main` 应与 `origin/main` 同步（https://github.com/877881029/Tasker ）。

## 当前目标

**任务改为 LocalAppData 下的 Markdown 文件；详情默认只读（Ctrl+I / Ctrl+S / Esc）**（已完成，冻结包已按此重建）

规格：`docs/superpowers/specs/2026-09-15-md-readonly-journal-design.md`  
计划：`docs/superpowers/plans/2026-09-15-md-readonly-journal.md`

## 下一步

1. 关掉旧的 Tasker 后，双击桌面快捷方式
2. 试用：只读打开、Ctrl+I 新记录、Ctrl+S、Esc、查找顶满

## 固定收尾（用户要求）

每次用户可见更新合入后，必须重打 `dist\Tasker\Tasker.exe` 并覆盖桌面 `Tasker.lnk`。未重打 exe 不算完成。

## 上一目标（已完成）

**详情贴在事项坞上，拖顶栏时一起移动**

## 背景

Tasker 是 Windows 桌面个人工作台。数据 `%LOCALAPPDATA%\Tasker\tasks\`。远程 https://github.com/877881029/Tasker

## 已完成

- v1、冻结、纸色坞、单实例、卡片只读详情编辑、气泡坞
- 2026-09-15：md 文件存储 + Reader 快捷键日志；冻结包已重建

## 阻塞项

- 无
