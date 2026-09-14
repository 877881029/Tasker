# Tasker 项目状态（AI 接手必读）

最后更新：2026-09-14  
Git：`main` 应与 `origin/main` 同步（https://github.com/877881029/Tasker ）。

## 当前目标

**Reader 同款桌面快捷方式**（已完成）

- 实现：已知文件夹桌面路径、图标 `,0`、AppUserModelID；优先指向 `dist\Tasker\Tasker.exe`；本机已覆盖写入 `Desktop\Tasker.lnk`
- 验证：全量 **33 passed**

## 下一步

1. 双击桌面 **Tasker** 试用（目标 `dist\Tasker\Tasker.exe`，蓝色 T）
2. 交互要改再开规格

## 上一目标（已完成）

**Tasker v1 工作台**（坞、详情、T 图标、SQLite）

## 背景

Tasker 是 Windows 桌面个人工作台。数据 `%LOCALAPPDATA%\Tasker\`。远程 https://github.com/877881029/Tasker

## 已完成

- v1 功能与图标
- 冻结构建脚本与包装测试 25 passed
- 2026-09-14：Reader 同款桌面 `Tasker.lnk`，指向冻结 exe

## 阻塞项

- 无
