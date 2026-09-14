# Tasker 项目状态（AI 接手必读）

最后更新：2026-09-14  
Git：`main` 应与 `origin/main` 同步（https://github.com/877881029/Tasker ）。

## 当前目标

**Tasker v1 已实现，等人试用**

- 规格：`docs/superpowers/specs/2026-09-14-tasker-design.md`
- 计划：`docs/superpowers/plans/2026-09-14-tasker.md`（6 个任务均已完成）
- 实现：右侧约 1/3 事项坞（查找、`+`、钉住、绿/红/灰）；左侧详情（置顶状态、Markdown 视觉/编辑、粘贴图、http 外开）；钴蓝色 T 图标；`scripts/setup.ps1` 装 venv 并启动 `-m tasker`。未冻结构建。
- 验证：`python -m pytest -v` → **21 passed**

## 下一步

1. 在仓库根执行 `.\scripts\setup.ps1`（或已有 venv 则 `.\.venv\Scripts\python.exe -m tasker`）试用
2. 需要冻结构建 `Tasker.exe` 时再开规格

## 背景

Tasker 是 Windows 桌面个人工作台。第一版扁平事项列表（待办绿 / 紧急红 / 完成灰），详情为 Markdown。数据在 `%LOCALAPPDATA%\Tasker\`（测试用 `TASKER_DATA_DIR`）。启动时可写桌面快捷方式（`TASKER_SKIP_SHELL_INTEGRATION=1` 可关）。

## 已完成

- 2026-09-14：产品设计定稿并写入规格
- 2026-09-14：规格补图标——Reader 同款钴蓝色圆角 **T**
- 2026-09-14：计划 Task 1–6 落地；pytest 21 passed
- 2026-09-14：远程与 Reader 同账号：https://github.com/877881029/Tasker

## 阻塞项

- 无
