# Tasker 项目状态（AI 接手必读）

最后更新：2026-09-15  
Git：`main` 应与 `origin/main` 同步（https://github.com/877881029/Tasker ）。

## 当前目标

**卡片只读、详情里编辑/改状态/删除**（已完成实现，待冻结包）

规格：`docs/superpowers/specs/2026-09-15-detail-only-edit-design.md`

- 点标题或便签打开详情；卡片上不能改标题、不能点圆改紧急
- 详情：标题、重要性圆、完成、删除

## 下一步

1. TDD 后冻结 exe

## 上一目标（已完成）

**圆点齐顶 + 圆角坞 + 单实例 + 空便签只留一条**

## 背景

Tasker 是 Windows 桌面个人工作台。数据 `%LOCALAPPDATA%\Tasker\`。远程 https://github.com/877881029/Tasker

## 已完成

- v1、冻结、任务栏 T、纸色坞、可拖动关闭、单实例、圆角坞

## 阻塞项

- 无
