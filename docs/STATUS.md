# Tasker 项目状态（AI 接手必读）

最后更新：2026-09-15  
Git：`main` 应与 `origin/main` 同步（https://github.com/877881029/Tasker ）。

## 当前目标

**UI 合同已锁死并入库**（供后续只优化布局，不改主题与接口）

合同：`docs/superpowers/specs/2026-09-15-ui-contract-lock.md`  
规则：`.cursor/rules/ui-theme-interface-lock.mdc`  
测试：`tests/test_ui_contract.py`

允许改间距/层次；禁止改 `theme.py` hex、Store/journal/paths 签名、快捷键语义、托盘/右 1/3 坞、任务 md 格式。

## 下一步

别人基于上述合同做 UI 打磨即可。主题和接口变更必须先另写规格并得到批准。

## 上一目标（已完成）

**工作台走系统托盘，不占任务栏按钮**（冻结包已重建）

## 固定收尾

用户可见更新必须重打 `dist\Tasker\Tasker.exe` 并覆盖桌面快捷方式。

## 背景

Tasker 是 Windows 桌面个人工作台。数据 `%LOCALAPPDATA%\Tasker\tasks\`。远程 https://github.com/877881029/Tasker

## 已完成

- v1、纸色坞、单实例、气泡详情、md 日志
- 2026-09-15：托盘工作台；UI 主题与接口合同锁死

## 阻塞项

- 无
