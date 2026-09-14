# Tasker 项目状态（AI 接手必读）

最后更新：2026-09-14  
Git：新仓库，尚无 `origin` 时先本地提交；一旦有远端必须把规格推到 `origin/main`。

## 当前目标

**按计划实现 Tasker v1**（连续做完，不在任务间停下来等人）

- 规格：`docs/superpowers/specs/2026-09-14-tasker-design.md`
- 计划：`docs/superpowers/plans/2026-09-14-tasker.md`（6 个任务）
- 用户确认：规格没问题；开始实现；汇报前不用暂停

## 下一步

执行计划 Task 1–6：包与 setup、T 图标、SQLite、右侧坞、详情 Markdown、接线 STATUS

## 背景

Tasker 是 Windows 桌面个人工作台。第一版只有扁平事项列表（待办绿 / 紧急红 / 完成灰），没有进度条、看板多列、账号或同步。详情复用 Reader 一类的 Markdown 视觉+编辑。数据在 `%LOCALAPPDATA%\Tasker\`（测试用 `TASKER_DATA_DIR`）。

仓库与 Reader 同节奏：`STATUS.md` + specs/plans 为权威；规格/计划/任务边界提交并推送。

## 已完成

- 2026-09-14：产品设计定稿并写入规格（无产品代码）
- 2026-09-14：规格补图标——Reader 同款钴蓝色圆角 **T**

## 阻塞项

- 尚无 `origin`。本机 `gh repo create Tasker --private` 失败：`Repository creation using enterprise-managed user account inside this enterprise is not allowed.` 需要在允许建库的账号/组织下建空库，再 `git remote add origin` 并推送 `main`。
