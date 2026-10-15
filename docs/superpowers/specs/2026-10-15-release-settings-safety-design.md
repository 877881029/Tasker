# 1.0.25：数据安全、设置页、发布与文档同步 设计

日期：2026-10-15　状态：用户已批准（同事视角评审第 1–11 项的处理决定）

## 1. 退出时不丢日志

- 托盘「退出」、`QApplication.aboutToQuit`、Windows 注销/关机（`commitDataRequest`）都先调用 `DockWindow.save_open_detail()`，把打开中的标题与日志同步写盘，再退出。

## 2. README 与实际一致

- README 只写真实存在的功能。日志只读视图为纯文本 + **可点击链接**（`http(s)://` 自动识别，系统浏览器打开）。不再声称 Markdown 渲染/粘贴图片。
- 删除无引用的 `preview/md_edit.py`、`MarkdownVisual`、`render_markdown`（`TaskerWebPage` 保留）。

## 3. 发布仓库与快速安装

- 新建公开仓库 `877881029/Tasker-releases`，只放 GitHub Release，资产为 `Tasker-<版本>-win64.zip`，**只保留最近 5 个版本**。
- `scripts/release.ps1`：读 `VERSION` → 打包 → 压缩 → 在发布仓库创建 `v<版本>` Release → 删除第 6 个及更早的 Release。
- `scripts/install.ps1`（同时上传到每个 Release）：下载最新 zip → 解压到 `%LOCALAPPDATA%\Programs\Tasker` → 创建桌面快捷方式 → 启动。一行安装：
  `irm https://github.com/877881029/Tasker-releases/releases/latest/download/install.ps1 | iex`

## 4–6. 依赖、文档、版本

- 依赖锁定为已验证版本（`PySide6==6.11.2` 等）。
- 版本号单一来源 `VERSION`，本次为 **1.0.25**；`pyproject` 动态读取，`version_info.txt` 由 `scripts/bump_version.py` 同步。之后**每次用户可见更新 patch +1**，并同步 `README.md`、`CHANGELOG.md`、`docs/STATUS.md`。
- `STATUS.md` 去重为「当前状态 + 历史摘要」；新增 `CHANGELOG.md`、`LICENSE`（MIT）、仓库描述与主题、README 截图。

## 8. 首次运行自动创建桌面快捷方式：保持不变。

## 9–10. 设置页

- 列表右上角新增齿轮按钮 `settingsBtn`（`+`、钉住、摘要切换之后），托盘菜单增加「设置」。
- 设置窗口仿 Copilot 设置：左侧分类导航，右侧为「标题 + 灰色说明 + 右侧控件」的行。
  - **通用**：显示日志摘要、DDL 到点提醒、开机自启。
  - **快捷键**：可改键——快速记录（全局）、新建、搜索、撤销删除、复制周报、写入日志、保存日志；固定键只读展示（Enter、Del、↑↓、Esc）。冲突或全局注册失败时行内提示并恢复原值；「恢复默认」。
  - **功能说明**：DDL、搜索关键词、摘要视图、周报、快速记录、删除与撤销、托盘。
  - **数据**：数据目录路径 + 打开文件夹、立即备份 + 打开备份文件夹、自动每日备份开关、版本号。
- 设置存 `settings.json`。

## 11. 数据安全

- 删除改为移入 **Windows 回收站**（5 秒内撤销仍有效）；测试环境（`TASKER_NO_RECYCLE=1`）直接删除。
- 每日首次启动自动备份 `tasks/` 为 zip 到「文档\Tasker\backups」，保留最近 7 份；设置里可关闭、可手动立即备份。
