# Tasker 项目状态（AI 接手必读）

最后更新：2026-09-15  
Git：`main` 应与 `origin/main` 同步（https://github.com/877881029/Tasker ）。

## 当前目标

**纸色坞 + 空白草稿单例**（已完成实现，待冻结包）

规格：`docs/superpowers/specs/2026-09-15-paper-dock-draft-design.md`  
计划：`docs/superpowers/plans/2026-09-15-paper-dock-draft.md`

- `+` / 启动：未填写的 pending 空行最多保留一条；点过色条或完成的空标题不算草稿
- 坞：纸色底、列表无白井；卡片便签间距；查找透明底留边框；加号透明；钉为图钉图标
- 验证：相关测试已绿（进程退出时 WebEngine 偶发 AV，与既有行为相同）

## 下一步

1. 关闭旧 Tasker，重新打冻结包后双击桌面快捷方式
2. 试用：连点 + 不应堆空任务；列表应是一张纸上的便签

## 上一目标（已完成）

**详情可保存/关闭 + 任务栏用 T 图标**

## 背景

Tasker 是 Windows 桌面个人工作台。数据 `%LOCALAPPDATA%\Tasker\`。远程 https://github.com/877881029/Tasker

## 已完成

- v1 功能与图标
- 冻结构建脚本与包装测试
- 2026-09-14：详情保存/关闭；任务栏强制 T 图标
- 2026-09-15：纸色坞与空白草稿单例

## 阻塞项

- 无
