# Tasker 项目状态（AI 接手必读）

最后更新：2026-09-17  
Git：`main` 应与 `origin/main` 同步（https://github.com/877881029/Tasker ）。

## 当前目标

**详情日志改成一整片编辑区（左时间、右正文）**（规格已写，待用户审阅后出计划）

- 规格：`docs/superpowers/specs/2026-09-17-journal-single-editor-design.md`
- 用户确认：方案 1；Ctrl+I 仍新开一条空记录；整篇（含新空位）同一编辑器可改
- 下一步：用户审阅规格 → 写 TDD 计划 → 实现（重打冻结包）

- 编辑框按真实视口宽度折行，高度含 descent / 边距，窗口变宽后会重算
- 条目间距仍约为两行字高

## 下一步

双击桌面 Tasker：打开较长日志，末行应完整可见，不应只露出半行。

## 上一目标（已完成）

**关闭详情保持坞位置；日志条目间距收成约两行**（冻结包已重建）

- Esc 收起详情后，坞回到打开详情前的坐标，不再弹回屏幕右侧初始位
- 两条日志之间的空隙约为两行字高，编辑框按内容高度收缩

## 上一目标（已完成）

**UI 合同已锁死并入库**

## 固定收尾

用户可见更新必须重打 `dist\Tasker\Tasker.exe` 并覆盖桌面快捷方式。

## 背景

Tasker 是 Windows 桌面个人工作台。数据 `%LOCALAPPDATA%\Tasker\tasks\`。远程 https://github.com/877881029/Tasker

## 已完成

- v1、纸色坞、单实例、气泡详情、md 日志
- 2026-09-15：托盘工作台；UI 主题与接口合同锁死

## 阻塞项

- `git push origin main` 失败：`Permission to 877881029/Tasker.git denied to runqyang_amdeng`（本地已提交 `cb777ac`，未同步远程）
