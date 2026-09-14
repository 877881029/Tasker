# Tasker 项目状态（AI 接手必读）

最后更新：2026-09-14  
Git：`main` 应与 `origin/main` 同步（https://github.com/877881029/Tasker ）。

## 当前目标

**setup.ps1 一次装好并冻结构建**

- 规格：`docs/superpowers/specs/2026-09-14-tasker-freeze-design.md`
- 计划：`docs/superpowers/plans/2026-09-14-tasker-freeze.md`
- 用户确认：开始开发；与 Reader 一样本机双击
- 实现：`tasker.spec` onedir（WebEngine + T 图标）；`scripts/build_windows.ps1`；`setup.ps1` 默认冻结，`-SkipBuild` 只跑源码；冻结构建把快捷方式指到 `Tasker.exe`
- 验证：`python -m pytest -v` → **25 passed**。本机 `scripts/build_windows.ps1` 已成功：`dist\Tasker\Tasker.exe`（3037681 bytes，不进 git）。

## 下一步

1. 双击 `C:\Research\AgentDevelopor\Tasker\dist\Tasker\Tasker.exe` 试用
2. 源码路径：`.\scripts\setup.ps1 -SkipBuild`
3. 交互要改再开规格

## 上一目标（已完成）

**Tasker v1 工作台**（坞、详情、T 图标、SQLite）

## 背景

Tasker 是 Windows 桌面个人工作台。数据 `%LOCALAPPDATA%\Tasker\`。远程 https://github.com/877881029/Tasker

## 已完成

- v1 功能与图标
- 冻结构建脚本与包装测试 25 passed

## 阻塞项

- 无
