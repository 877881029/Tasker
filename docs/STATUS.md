# Tasker 项目状态（AI 接手必读）

最后更新：2026-09-15  
Git：`main` 应与 `origin/main` 同步（https://github.com/877881029/Tasker ）。

## 当前目标

**工作台走系统托盘，不占任务栏按钮**（已完成，冻结包已按此重建）

规格：`docs/superpowers/specs/2026-09-15-tray-not-taskbar-design.md`

- `Qt.Tool` 无任务栏按钮；托盘图标左键显示，右键退出
- 坞上 × 只隐藏窗口，进程留在托盘
- Windows「隐藏的图标」由系统设置决定，程序无法强制塞进 overflow

## 下一步

1. 双击桌面 Tasker；任务栏不应再有常驻按钮，看托盘/隐藏图标里的 T
2. × 收起坞；托盘「显示」再打开，「退出」才结束进程

## 上一目标（已完成）

**Markdown 文件存储 + Ctrl+I / Ctrl+S / Esc**

## 固定收尾

用户可见更新必须重打 `dist\Tasker\Tasker.exe` 并覆盖桌面快捷方式。

## 背景

Tasker 是 Windows 桌面个人工作台。数据 `%LOCALAPPDATA%\Tasker\tasks\`。远程 https://github.com/877881029/Tasker

## 已完成

- v1、纸色坞、单实例、气泡详情、md 日志
- 2026-09-15：托盘工作台（不占任务栏）

## 阻塞项

- 无
