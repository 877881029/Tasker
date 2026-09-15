# Tasker 项目状态（AI 接手必读）

最后更新：2026-09-15  
Git：`main` 应与 `origin/main` 同步（https://github.com/877881029/Tasker ）。

## 当前目标

**便签卡片 + 详情完成/删除**（已完成实现，待冻结包）

规格：`docs/superpowers/specs/2026-09-15-note-card-detail-actions-design.md`

- 卡片：实心圆（绿/红/灰）+ 可换行标题（高 ≥72）；悬停亮起；未聚焦时点标题进详情；无详情按钮、无完成勾
- 详情：完成、删除；删除后关窗并刷新列表
- 验证：window/detail/store 测试已绿

## 下一步

1. 关闭旧 Tasker，打冻结包后双击桌面快捷方式
2. 试用：点标题进详情、完成、删除、长标题换行

## 上一目标（已完成）

**纸色坞 + 空白草稿单例**

## 背景

Tasker 是 Windows 桌面个人工作台。数据 `%LOCALAPPDATA%\Tasker\`。远程 https://github.com/877881029/Tasker

## 已完成

- v1 功能与图标、冻结、任务栏 T、纸色坞与空白草稿单例

## 阻塞项

- 无
