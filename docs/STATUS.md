# Tasker 项目状态（AI 接手必读）

最后更新：2026-09-14  
Git：新仓库，尚无 `origin` 时先本地提交；一旦有远端必须把规格推到 `origin/main`。

## 当前目标

**把已批准的 Tasker 工作台规格落成可执行计划**（尚未写计划）

- 规格：`docs/superpowers/specs/2026-09-14-tasker-design.md`（用户已在对话中批准设计全文）
- 产品：本机 PySide6 右侧约 1/3 事项栏 + 左侧详情；SQLite；Markdown 详情可粘贴图和超链接
- 用户确认：独立仓库与 Reader 同级；不跑 Docker / Vikunja；布局 A+；`+` 新建；色条绿↔红；勾选完成灰底不划线；钉住置顶

## 下一步

用户审阅规格文件；通过后写 TDD 实施计划 `docs/superpowers/plans/2026-09-14-tasker.md`，再实现 `scripts/setup.ps1` 与最小窗口

## 背景

Tasker 是 Windows 桌面个人工作台。第一版只有扁平事项列表（待办绿 / 紧急红 / 完成灰），没有进度条、看板多列、账号或同步。详情复用 Reader 一类的 Markdown 视觉+编辑。数据在 `%LOCALAPPDATA%\Tasker\`（测试用 `TASKER_DATA_DIR`）。

仓库与 Reader 同节奏：`STATUS.md` + specs/plans 为权威；规格/计划/任务边界提交并推送。

## 已完成

- 2026-09-14：产品设计定稿并写入规格（无产品代码）

## 阻塞项

- 尚无 `origin`。需要 GitHub 远程（账号下与 Reader 同级的 `Tasker` 库）之后，未推送的提交才算同步完成。
