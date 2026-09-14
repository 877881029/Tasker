# Tasker 项目状态（AI 接手必读）

最后更新：2026-09-14  
Git：`main` 应与 `origin/main` 同步（https://github.com/877881029/Tasker ）。

## 当前目标

**详情可保存/关闭 + 任务栏用 T 图标**（已完成）

- 详情顶栏「保存」「关闭」，Esc / 窗口关闭都会先存再关；详情用 Tool 窗，不占第二条任务栏
- 新建只落在右侧列表改标题，点「详情」再开左边；不再一点标题就弹详情把人困住
- 任务栏：DWM 强制图标 + AppUserModelID / 重开命令，避免用窗口快照当图标
- 验证：全量 **35 passed**（进程退出时 WebEngine 偶发 AV，与 Reader 同类，测试已绿）

## 下一步

1. 关闭正在跑的旧 Tasker，再双击桌面快捷方式（已指向刚打好的 `dist\Tasker\Tasker.exe`）
2. 试用：+ 建任务、详情保存/关闭、看任务栏是否为蓝色 T

## 上一目标（已完成）

**Tasker v1 工作台**（坞、详情、T 图标、SQLite）

## 背景

Tasker 是 Windows 桌面个人工作台。数据 `%LOCALAPPDATA%\Tasker\`。远程 https://github.com/877881029/Tasker

## 已完成

- v1 功能与图标
- 冻结构建脚本与包装测试 25 passed
- 2026-09-14：Reader 同款桌面 `Tasker.lnk`，指向冻结 exe
- 2026-09-14：详情保存/关闭；任务栏强制 T 图标
- 2026-09-14：冻结包已按上述 UX 重建（`dist\Tasker\Tasker.exe`）

## 阻塞项

- 无
