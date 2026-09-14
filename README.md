# Tasker

本机 Windows 工作台：屏幕右侧约三分之一列出当前事项，点开后在左侧编辑详情（Markdown、粘贴图片、超链接）。图标是与 Reader 同系列的钴蓝色大写 **T**。不使用 Docker，不运行 Vikunja。

## 怎么跑

需要 Python 3.12+。在仓库根：

```powershell
.\scripts\setup.ps1
```

会装依赖、打出 `dist\Tasker\Tasker.exe` 并启动。只要源码、不要冻结构建：

```powershell
.\scripts\setup.ps1 -SkipBuild
```

只要装环境、不要弹窗：

```powershell
.\scripts\setup.ps1 -SkipLaunch
```

数据目录：`%LOCALAPPDATA%\Tasker\`。测试时设 `TASKER_DATA_DIR`。不要创建桌面快捷方式时设 `TASKER_SKIP_SHELL_INTEGRATION=1`。

详情：`Ctrl+I` 编辑 Markdown，`Ctrl+T` 回到视觉预览（会先保存正文）。

## 给接手的人 / Agent

1. `docs/STATUS.md`
2. `docs/superpowers/process.md`
3. `docs/superpowers/specs/2026-09-14-tasker-design.md`
4. `docs/superpowers/plans/2026-09-14-tasker.md`
