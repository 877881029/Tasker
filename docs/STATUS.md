# Tasker 项目状态（AI 接手必读）

最后更新：2026-09-17  
Git：`main` 应与 `origin/main` 同步（https://github.com/877881029/Tasker ）。

## 当前目标

**打开详情不挪任务栏；纸窗可拖可缩放**（规格待你确认）

- 规格：`docs/superpowers/specs/2026-09-17-dock-place-drag-resize-design.md`
- 点卡片：任务栏 x/y/宽/高不变，详情向左加宽（默认约两倍栏宽，之后记住）
- 空白纸面拖整窗；四边四角缩放

## 下一步

请审阅上述规格；确认后再写实施计划。

## 上一目标（已完成）

**只读日志改用 Reader 同一套 Chromium 渲染**（已完成，冻结包已重建）

- 只读：`QWebEngineView` + `wrap_document_html`（Candara 16px / 行高 1.72 / `#1c1915`）
- 时间戳一列 CSS grid（`7.75rem` + 正文 `minmax(0,1fr)`），折行不再挤进时间列
- Ctrl+I 仍切回整篇 `JournalEditor`

## 下一步

双击桌面 Tasker：详情只读应与 Reader 文档同样字重、墨色；时间戳完整右对齐成一列，不应只剩「M」。

## 上一目标（已完成）

**只读日志时间戳对齐成一列**（已完成，冻结包已重建）

- 一张表固定左列 118px；折行留在正文列，不再钻到时间下面

## 下一步

双击桌面 Tasker：时间戳应上下对齐，长句折行只在右侧。

## 上一目标（已完成）

**日志阅读态改用 Reader 文档 CSS**（冻结包已重建）

- 只读：QTextBrowser + `document_style`（16px / 行高 1.72 / Candara / `#1c1915`）
- Ctrl+I 仍切回整篇编辑器

## 下一步

双击桌面 Tasker：打开详情只读，正文应与 Reader 文档页同样深、同样大。

## 上一目标（已完成）

**日志正文对齐 Reader 墨色**（冻结包已重建）

- 只读日志不再发灰：12pt Candara、行高 1.72、视口铺实纸色
- 时间戳仍用 COBALT / MUTED，正文锁 `#1c1915`

## 下一步

双击桌面 Tasker：详情正文应与 Reader 文档一样深，不应发浅灰。

## 上一目标（已完成）

**详情日志展开与排版打磨**（冻结包已重建）

- 规格：`docs/superpowers/specs/2026-09-17-detail-expand-journal-polish-design.md`
- 点卡片从当前坞位置向左展开，轨道右缘不动
- Ctrl+I 未写入则保存时丢掉空时间戳
- 记录之间一空行；正文/时间戳统一 Candara/Calibri/Segoe UI

## 下一步

双击桌面 Tasker：拖开坞再点卡片，轨道不应右跳；空 Ctrl+I 后 Esc 不应留下时间戳。

## 上一目标（已完成）

**详情日志改成一整片编辑区（左时间、右正文）**（冻结包已重建）

- 规格：`docs/superpowers/specs/2026-09-17-journal-single-editor-design.md`
- 计划：`docs/superpowers/plans/2026-09-17-journal-single-editor.md`
- 阅读区一个折行编辑器，左侧时间 gutter；Ctrl+I 仍新开空记录，之后整篇可改

## 下一步

双击桌面 Tasker：打开详情，Ctrl+I 后应能改旧记录；长文折行不再切半行。

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

- `git push origin main` 失败：`Permission to 877881029/Tasker.git denied to runqyang_amdeng`（本地已提交，未同步远程）
