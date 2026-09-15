# Tasker 项目状态（AI 接手必读）

最后更新：2026-09-15  
Git：`main` 应与 `origin/main` 同步（https://github.com/877881029/Tasker ）。

## 当前目标

**任务改为 LocalAppData 下的 Markdown 文件；详情默认只读（Ctrl+I / Ctrl+S / Esc）**（规格已写，待你审阅文件后再写实施计划）

规格：`docs/superpowers/specs/2026-09-15-md-readonly-journal-design.md`

- 一件任务一个 `tasks\<id>.md`（YAML：title / state），不要新的 SQLite
- 打开只读；Ctrl+I 新开一条记录（同一小时也不合并）；Ctrl+S 保存后仍只读；Esc 保存并收起气泡
- 去掉保存/关闭；去掉坞上「事项」，查找顶满
- 图片按 md 里的原路径读，不搬文件

## 下一步

1. 你审阅上述规格；要改先说
2. 通过后写 TDD 实施计划并实现

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
