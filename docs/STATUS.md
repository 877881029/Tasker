# Tasker 项目状态（AI 接手必读）

最后更新：2026-10-15　·　**当前版本 1.0.25**　·　Git：`main` 与 `origin/main` 同步（https://github.com/877881029/Tasker ）

## 当前状态

**1.0.25：数据安全、设置页、快速安装**（已完成 2026-10-15，已部署：双击桌面 Tasker；已发布到 Tasker-releases）

- 退出 / 注销前保存打开中的日志；删除进回收站；每日自动备份（文档\Tasker\backups，保留 7 份）
- 设置窗口（齿轮按钮 / 托盘「设置…」）：通用开关、全部快捷键可改、功能说明、数据与备份
- 只读日志链接可点击；删除未使用的 Markdown 预览代码
- 发布仓库 `877881029/Tasker-releases`（保留最近 5 版）+ 一行安装 `irm .../latest/download/install.ps1 | iex`
- 版本单一来源 `VERSION`；依赖锁定；新增 CHANGELOG、LICENSE（MIT）
- 规格：`docs/superpowers/specs/2026-10-15-release-settings-safety-design.md`
- 计划：`docs/superpowers/plans/2026-10-15-release-settings-safety.md`

## 下一步

- 无进行中任务。候选：发布包瘦身（去掉 WebEngine devtools 资源约 80 MB）、CI 自动跑测试。

## 每次更新必做（固定收尾）

1. `python scripts\bump_version.py`（patch +1），更新 `CHANGELOG.md`、`README.md` 顶部版本、本文件。
2. 全量测试：`.\.venv\Scripts\python.exe -m pytest -q`（不要加 `-p`）。
3. 打包并发布：`.\scripts\release.ps1`（含打包；只保留最近 5 个 Release）。
4. 本机部署：停掉 `%LOCALAPPDATA%\Programs\Tasker\Tasker.exe`，`robocopy dist\Tasker` 过去，刷新桌面快捷方式。
5. 提交并推送 `origin/main`（账号 `877881029`）。

## 背景

Tasker 是 Windows 桌面个人任务 + 工作日志。数据 `%LOCALAPPDATA%\Tasker\tasks\*.md`。UI 合同：`docs/superpowers/specs/2026-09-15-ui-contract-lock.md`。

## 历史

详见 `CHANGELOG.md` 与 `docs/superpowers/specs/`。要点：

- 2026-10-12：紧急任务 DDL；便捷功能包 10 项；摘要/简约切换；粘贴段落修复
- 2026-10-10：Copilot 浅色主题与详情体验；窗口拖动/缩放/屏幕自适应
- 2026-09：托盘工作台、单实例、Markdown 存储、日志单编辑器、UI 合同锁定

## 已知注意事项

- pytest 不要加 `-p ...`：QtWebEngine 解析命令行会崩（退出码 -536870873）。
- 打包路径过长：`release.ps1` 自动用 `subst` 短盘符构建。
- 本机 `Win+Alt+T` 被系统占用，快速记录回退为 `Ctrl+Alt+T`（可在设置里改）。

## 阻塞项

- 无。推送用 GitHub 账号 `877881029`（环境里有 amdeng 的 `GH_TOKEN` 时先清掉并 `gh auth switch -u 877881029`）。
