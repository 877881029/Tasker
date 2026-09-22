# Tasker 项目状态（AI 接手必读）

最后更新：2026-09-22  
Git：`main` 应与 `origin/main` 同步（https://github.com/877881029/Tasker ）。

## 当前目标

**UI 成熟度打磨**（已完成，冻结包已重建并部署）

- 日志读/写/已保存状态可见，保留 `Ctrl+I / Ctrl+S / Esc`
- 卡片支持键盘焦点及 Enter/Space，控件补齐无障碍名称和确定性 tab 顺序
- 无事项、无搜索结果与托盘隐藏语义明确
- 删除在原标题栏内四秒两步确认，不增加弹窗或新按钮
- 顶层纸窗关闭时销毁完整 Qt 子树，Python 3.12 全量测试退出码恢复为 0
- Windows 构建脚本支持 `TASKER_BUILD_VENV` 短路径环境
- Impeccable 视觉北极星：「桌边工作纸」
- 规格：`docs/superpowers/specs/2026-09-22-ui-maturity-polish-design.md`
- 计划：`docs/superpowers/plans/2026-09-22-ui-maturity-polish.md`
- 产品与视觉事实：`PRODUCT.md`、`DESIGN.md`
- 验证：Python 3.12 `93 passed`；冻结包与图标完整；原生折叠、无结果、展开、写入、保存和删除确认状态通过
- 部署：`%LOCALAPPDATA%\Programs\Tasker\Tasker.exe`；桌面 `Tasker.lnk` 已覆盖

## 下一步

双击桌面 Tasker 做日常验收：卡片可用键盘打开，Ctrl+I/Ctrl+S 状态提示正确，删除第一次只进入“确认删除”且四秒后复位。

## 上一目标（已完成）

**纸窗四角对齐**（已完成，冻结包已重建）

- 未铺满时 HWND 圆角遮罩贴齐整窗（16px，不再收 1px），去掉四角发黑/错位
- 铺满工作区时仍清遮罩、圆角 0，四边四角可拉不变
- 规格：`docs/superpowers/specs/2026-09-21-fill-resize-layout-design.md`

## 下一步

双击桌面 Tasker：折叠栏四个圆角应贴齐、不应发黑；铺满工作区后仍可从边角拉小。

## 上一目标（已完成）

**Ctrl+S 改回编辑器写入，不再从 Chromium 读正文**（已完成，冻结包已重建）

- 真正原因：打字在 `contenteditable`，保存读不到页面；多次 JS/脏标记/快照补丁后 Ctrl+S 仍清空
- 只读仍用 Chromium；Ctrl+I 切回 `JournalEditor`，保存读同一块编辑器（与原先能用的写入逻辑一致）
- 规格：`docs/superpowers/specs/2026-09-17-detail-expand-journal-polish-design.md` 第 6 条

## 下一步

双击桌面 Tasker：打开详情，Ctrl+I 打几个字再 Ctrl+S，编辑区不应被清空，字应留在日志里。

## 上一目标（已完成）

**Ctrl+S 必须用输入过程中同步好的 Chromium 正文**（已完成，冻结包已重建）

- 真正原因：字打在 Chromium 里，保存却在快捷键里 nested `runJavaScript`；这次读取经常是空的，隐藏编辑器仍是空时间戳，丢掉后看起来像没保存
- 旧逻辑没问题是因为打字和保存都走 `QPlainTextEdit`；改成 contenteditable 之后保存不再读用户正在打的那个面
- 写入时轮询页面行到 Python `live_rows`，Ctrl+S 先用这份快照
- 规格：`docs/superpowers/specs/2026-09-17-detail-expand-journal-polish-design.md` 第 6 条

## 下一步

双击桌面 Tasker：打开详情，Ctrl+I 打「开始测试」再 Ctrl+S，这几个字应留在日志里。

## 上一目标（已完成）

**Ctrl+S 不得用空 DOM 把日志抹掉**（已完成，冻结包已重建）

- 真正原因：保存把 Chromium 行整页写回；页面未排版时 `innerText` 全空，空时间戳再被丢掉，旧记录也从磁盘消失
- 有正文的行才采用页面文字；整页空白或某行被读成空时，保留编辑器里已有内容
- 规格：`docs/superpowers/specs/2026-09-17-detail-expand-journal-polish-design.md` 第 6 条

## 下一步

双击桌面 Tasker：打开已有记录的卡片，Ctrl+I 写入后再 Ctrl+S，旧内容应还在，刚打的字也应留下。

## 上一目标（已完成）

**Ctrl+S 必须收下详情里刚写的字**（已完成，冻结包已重建）

- 真正原因：写入在 Chromium `contenteditable` 上，保存却只在 `_journalDirty` 为真时才把 DOM 写回隐藏编辑器；`loadFinished` 竞态下脏标记经常没亮
- 保存时只要读到页面行就提交，不再看脏标记；JS 读不到行则保留编辑器模型，空时间戳仍在提交后再丢
- 规格：`docs/superpowers/specs/2026-09-17-detail-expand-journal-polish-design.md` 第 6 条

## 下一步

双击桌面 Tasker：打开详情，Ctrl+I 写入后再 Ctrl+S，刚打的字应留在日志里，不应像没保存就退出编辑。

## 上一目标（已完成）

**写入态与只读共用 Chromium**（已完成，冻结包已重建）

- 真正原因：Ctrl+I 切到 `QPlainTextEdit`，Qt 光栅化对不齐 WebEngine
- 写入仍在 `QWebEngineView` 上 `contenteditable`，同一套 Candara 16px / 1.72 / INK

## 下一步

双击桌面 Tasker：Ctrl+I 后正文应与只读同一套字，不再变细变浅。

## 上一目标（已完成）

**写入态日志对齐只读 Chromium 字号**（已完成，冻结包已重建）

- 编辑器正文 Candara 16px / 行高 1.72 / `#1c1915`；时间戳 13px、字重 600
- 详情页不再用 12pt 把写入态压回去

## 下一步

双击桌面 Tasker：Ctrl+I 写入时正文和时间戳应与只读同样大、同样深。

## 上一目标（已完成）

**打开详情不挪任务栏；纸窗可拖可缩放**（已完成，冻结包已重建）

- 规格：`docs/superpowers/specs/2026-09-17-dock-place-drag-resize-design.md`
- 计划：`docs/superpowers/plans/2026-09-17-dock-place-drag-resize.md`
- 点卡片：任务栏 x/y/宽/高不变，详情向左加宽（默认约两倍栏宽，之后记住）
- 空白纸面拖整窗；四边四角缩放

## 下一步

双击桌面 Tasker：把坞拖到别处再点卡片，任务栏不应弹回初始位置；空白纸面可拖，边缘可缩放。

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

**日志正文对齐 Reader 墨色**（已完成，冻结包已重建）

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

- 无。`origin/main` 用 GitHub 账号 `877881029` 推送（不要用 `runqyang_amdeng`）。
