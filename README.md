# Tasker

本机 Windows 工作台：屏幕右侧约三分之一列出当前事项，点开后在左侧编辑详情（Markdown、粘贴图片、超链接）。不使用 Docker，不运行 Vikunja。

## 当前状态

规格已定：`docs/superpowers/specs/2026-09-14-tasker-design.md`。活进度在 `docs/STATUS.md`。源码与 `scripts/setup.ps1` 尚未落地。

## 以后怎么跑

实现第一刀之后，clone 本仓库，在仓库根执行：

```powershell
.\scripts\setup.ps1
```

会创建 `.venv`、安装依赖并启动 Tasker。只要源码、不要自动启动时再加开关（与 Reader 相同思路）。

## 给接手的人 / Agent

1. `docs/STATUS.md`
2. `docs/superpowers/process.md`
3. 当前规格与（若已有）`docs/superpowers/plans/`
