# Tasker 项目状态（AI 接手必读）

最后更新：2026-09-15  
Git：`main` 应与 `origin/main` 同步（https://github.com/877881029/Tasker ）。

## 当前目标

**任务改为 LocalAppData 下的 Markdown 文件；详情默认只读（Ctrl+I / Ctrl+S / Esc）**（实现完成，待你本地点开确认）

规格：`docs/superpowers/specs/2026-09-15-md-readonly-journal-design.md`  
计划：`docs/superpowers/plans/2026-09-15-md-readonly-journal.md`

- 一件任务一个 `tasks\<id>.md`
- 打开只读；Ctrl+I 新开一条；Ctrl+S 保存后仍只读；Esc 保存并收起
- 坞顶栏无「事项」，查找顶满
- 旧 sqlite 仅在 `tasks\` 为空时迁一次

## 下一步

1. 运行 `python -m tasker`（冻结包尚未按此重打）
2. 试用快捷键与 md 文件；需要桌面快捷方式跟上时再打 `scripts/build_windows.ps1`

## 上一目标（已完成）

**详情贴在事项坞上，拖顶栏时一起移动**

## 背景

Tasker 是 Windows 桌面个人工作台。数据 `%LOCALAPPDATA%\Tasker\tasks\`。远程 https://github.com/877881029/Tasker

## 已完成

- v1、冻结、纸色坞、单实例、卡片只读详情编辑、气泡坞
- 2026-09-15：md 文件存储 + Reader 快捷键日志（源码已合入）

## 阻塞项

- 无
