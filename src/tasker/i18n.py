"""Tiny UI translation layer. Source strings are Chinese; English lives in EN.

The language is chosen once at startup (settings.json "language"); switching it
in Settings restarts Tasker so every widget is built in the new language.
"""
from __future__ import annotations

LANGUAGES = (("zh", "中文"), ("en", "English"))
_current = "zh"


def set_language(code: str) -> None:
    global _current
    _current = code if code in dict(LANGUAGES) else "zh"


def language() -> str:
    return _current


def tr(_text: str, /, **values) -> str:
    template = EN.get(_text, _text) if _current == "en" else _text
    return template.format(**values) if values else template


EN: dict[str, str] = {
    # states
    "普通": "Normal",
    "紧急": "Urgent",
    "已完成": "Done",
    "无标题": "Untitled",
    "标题": "Title",
    # deadline
    "超期 {left}": "Overdue {left}",
    "今天 18:00": "Today 18:00",
    "明天 18:00": "Tomorrow 18:00",
    "3 天后 18:00": "In 3 days 18:00",
    "下周一 09:00": "Next Monday 09:00",
    "自定义：滚轮或方向键调整，回车确定": "Custom: scroll or arrow keys, Enter to apply",
    "清除 DDL": "Clear DDL",
    "设置 DDL  ▾": "Set DDL  ▾",
    "截止时间：未设置": "Deadline: not set",
    "截止时间：{label}": "Deadline: {label}",
    "设置截止时间（仅紧急任务）": "Set a deadline (urgent tasks only)",
    "打开菜单选择或清除截止时间": "Open the menu to pick or clear a deadline",
    "截止倒计时 {text}": "Time left {text}",
    # reminders
    "已超期": "Overdue",
    "即将截止": "Due soon",
    "{name} · 剩余 {left}": "{name} · {left} left",
    "有 {count} 个任务已超期": "{count} task(s) overdue",
    # report
    "[图片]": "[image]",
    "# 周报 {start} ~ {end}": "# Weekly report {start} ~ {end}",
    "本周暂无记录": "No entries this week",
    # shortcuts
    "快速记录": "Quick capture",
    "在任何程序里弹出输入框，回车即记下一条任务": "Pop up an input box from any app; Enter saves a task",
    "新建任务": "New task",
    "新建一条任务并打开详情": "Create a task and open its details",
    "查找": "Search",
    "跳到搜索框": "Jump to the search box",
    "撤销删除": "Undo delete",
    "删除后 5 秒内恢复": "Restore within 5 seconds of deleting",
    "复制本周周报": "Copy weekly report",
    "把本周日志汇总成 Markdown 复制到剪贴板": "Copy this week's log entries as Markdown",
    "写入日志": "Write log",
    "在详情里新增一条带时间戳的日志": "Add a time-stamped log entry in details",
    "保存日志": "Save log",
    "保存并回到只读视图": "Save and return to the read view",
    "Enter / 空格": "Enter / Space",
    "打开选中的任务": "Open the selected task",
    "在搜索框和任务之间移动": "Move between the search box and tasks",
    "删除选中的任务（进入回收站，5 秒内可撤销）": "Delete the selected task (Recycle Bin, undo within 5 s)",
    "收起详情；详情未打开时隐藏到托盘（钉住时不隐藏）": "Close details; otherwise hide to tray (not when pinned)",
    "右键 / 菜单键": "Right-click / Menu key",
    "改状态、设置 DDL": "Change status, set DDL",
    "{keys} 已固定用于列表操作": "{keys} is reserved for list navigation",
    "需要配合 Ctrl / Alt / Shift / Win 使用": "Add Ctrl / Alt / Shift / Win",
    "与「{name}」冲突": "Already used by \"{name}\"",
    "{keys} 已被其它程序占用，请换一个组合": "{keys} is taken by another app; try another combination",
    # detail
    "{write} 写入 · {save} 保存 · Esc 收起": "{write} write · {save} save · Esc close",
    "正在写入 · {save} 保存 · Esc 保存并收起": "Writing · {save} save · Esc save and close",
    "已保存 {time} · {write} 继续写入 · Esc 收起": "Saved {time} · {write} write more · Esc close",
    "详情": "Details",
    "改状态：普通 / 紧急 / 已完成": "Status: Normal / Urgent / Done",
    "打开菜单选择普通、紧急或已完成": "Open the menu to choose Normal, Urgent or Done",
    "任务标题": "Task title",
    "日志操作状态": "Log status",
    "删除": "Delete",
    "删除任务": "Delete task",
    "任务状态：{label}": "Status: {label}",
    "任务日志只读内容": "Task log",
    "任务日志编辑器": "Task log editor",
    "记录…": "Write…",
    # quick capture
    "回车保存 · Esc 取消 · 以 ! 开头设为紧急": "Enter saves · Esc cancels · start with ! for urgent",
    "记一件事…": "Jot something down…",
    "快速记录任务标题": "Quick capture title",
    # dock
    "搜索标题和日志；也可输入：紧急、普通、已完成、超期、今天、DDL": "Search titles and logs; or type: urgent, normal, done, overdue, today, DDL",
    "拖动调整宽度": "Drag to resize",
    "{state}任务：{name}": "{state} task: {name}",
    "按 Enter 或空格打开详情，菜单键或右键改状态": "Enter or Space opens details; Menu key or right-click changes status",
    "{state} · {name} · 右键改状态": "{state} · {name} · right-click to change status",
    "查找任务或日志…": "Search tasks or logs…",
    "搜索事项": "Search tasks",
    "新建事项": "New task",
    "钉在其它窗口上面": "Keep on top of other windows",
    "置顶窗口": "Pin window",
    "显示日志摘要": "Show log summary",
    "显示最新日志摘要": "Show the latest log line",
    "设置：功能说明、快捷键、数据与备份": "Settings: features, shortcuts, data and backup",
    "设置": "Settings",
    "显示": "Show",
    "设置…": "Settings…",
    "开机自启": "Start with Windows",
    "退出": "Quit",
    "快速记录（{label}）": "Quick capture ({label})",
    "切换为简约列表（只显示标题）": "Switch to the compact list (titles only)",
    "已记录": "Saved",
    "已复制本周周报": "Weekly report copied",
    "{count} 个任务": "{count} task(s)",
    "Tasker · {count} 个任务已超期": "Tasker · {count} task(s) overdue",
    "没有找到匹配事项\n换个关键词试试": "No matching tasks\nTry another keyword",
    "没有找到匹配事项": "No matching tasks",
    "还没有事项\n点 + 开始记录": "No tasks yet\nClick + to start",
    "还没有事项": "No tasks yet",
    "已完成 ({count})  {arrow}": "Done ({count})  {arrow}",
    "已完成 {count} 项，收起": "{count} done, collapse",
    "已完成 {count} 项，展开": "{count} done, expand",
    "已删除「{name}」": "Deleted \"{name}\"",
    "撤销": "Undo",
    "{title}：{body}": "{title}: {body}",
    # settings window
    "Tasker 设置": "Tasker Settings",
    "关闭": "Close",
    "通用": "General",
    "快捷键": "Shortcuts",
    "功能说明": "Features",
    "数据": "Data",
    "版本 {version}": "Version {version}",
    "搜索设置…": "Search settings…",
    "没有匹配的设置": "No matching settings",
    "常用开关和界面语言。": "Everyday switches and display language.",
    "点按快捷键后按下新组合；Esc 取消。": "Click a shortcut, then press the new combination; Esc cancels.",
    "Tasker 的主要功能和用法。": "What Tasker does and how to use it.",
    "数据只保存在本机；删除进入回收站，并每天自动备份。": "Data stays on this PC; deletions go to the Recycle Bin and a backup runs daily.",
    "界面": "Interface",
    "提醒与启动": "Reminders and startup",
    "语言": "Language",
    "界面语言。切换后需要重启 Tasker。": "Display language. Tasker restarts to apply it.",
    "切换后需要重启 Tasker 才能生效。": "Restart Tasker to apply the new language.",
    "立即重启": "Restart now",
    "在任务标题下显示最新一条日志；关闭为只显示标题的简约列表。": "Show the latest log line under each title; off shows titles only.",
    "DDL 到点提醒": "Deadline reminders",
    "截止前 1 小时和超期时弹出系统通知。": "Notify one hour before a deadline and when it passes.",
    "登录 Windows 后自动在托盘启动 Tasker。": "Start Tasker in the tray when you sign in to Windows.",
    "写入注册表失败": "Could not write to the registry",
    "可自定义": "Customizable",
    "固定按键": "Fixed keys",
    "（全局，在任何程序中都可用）": " (global, works in any app)",
    "恢复默认": "Restore defaults",
    "把以上快捷键全部恢复为默认组合。": "Reset all shortcuts above to their defaults.",
    "未设置": "Not set",
    "自动": "Automatic",
    "按下新快捷键…": "Press new shortcut…",
    "快捷键 {keys}，点按后按下新组合": "Shortcut {keys}; click, then press a new combination",
    "自动：依次尝试 {auto}，当前生效 {active}": "Automatic: tries {auto}; active: {active}",
    "无": "none",
    "存储": "Storage",
    "数据目录": "Data folder",
    "打开文件夹": "Open folder",
    "删除的任务进入 Windows 回收站，可从回收站还原。": "Deleted tasks go to the Windows Recycle Bin and can be restored from there.",
    "备份": "Backup",
    "每日自动备份": "Daily backup",
    "每天第一次启动时把全部任务打包成 zip，保留最近 7 份。": "Zip all tasks on the first start each day; keep the latest 7.",
    "备份位置": "Backup folder",
    "立即备份": "Back up now",
    "打开备份文件夹": "Open backup folder",
    "最近一次 {stamp}": "Last backup {stamp}",
    "关于": "About",
    "版本": "Version",
    "查看发布版本": "View releases",
    # features
    "状态与 DDL": "Status and DDL",
    "右键任务或点详情左上角胶囊改状态：普通 / 紧急 / 已完成。紧急任务可设 DDL，列表右侧显示倒计时（如 03d-14h-57m），紧急任务按 DDL 先后排序；不足 24 小时变红，超期显示红底。":
        "Right-click a task or use the pill in details to set Normal / Urgent / Done. Urgent tasks can have a DDL: the list shows a countdown (e.g. 03d-14h-57m) and sorts by deadline; under 24 h turns red, overdue gets a red badge.",
    "到点提醒": "Reminders",
    "截止前 1 小时和超期时各弹一次系统通知，点通知直接打开任务；托盘图标右下角红点显示超期数量。":
        "A notification one hour before and when a deadline passes; click it to open the task. The tray icon shows the overdue count.",
    "日志": "Log",
    "详情里每条日志带时间戳，最新在上。写入后保存；只读视图里的 http/https 链接可点击，用浏览器打开。":
        "Each log entry in details is time-stamped, newest first. Links (http/https) in the read view open in your browser.",
    "按全局快捷键弹出输入框，回车即建任务，不打开详情；以 ! 开头直接设为紧急。":
        "The global shortcut pops up an input box; Enter creates a task without opening details. Start with ! for urgent.",
    "搜索": "Search",
    "搜索标题和日志正文；也可输入关键词筛选：紧急、普通、已完成、超期、今天、DDL。":
        "Searches titles and log text. Keywords filter too: urgent, normal, done, overdue, today, DDL.",
    "摘要视图": "Summary view",
    "右上角列表按钮切换：简约（只显示标题）或在标题下显示最新一条日志。":
        "The list button at the top right switches between titles only and titles with the latest log line.",
    "已完成折叠": "Collapsed done tasks",
    "已完成任务收在列表底部「已完成 (N)」，点一下展开；搜索时自动展开。":
        "Done tasks fold into \"Done (N)\" at the bottom; click to expand. Searching expands them.",
    "删除与撤销": "Delete and undo",
    "删除的任务进入 Windows 回收站；5 秒内点「撤销」或按撤销快捷键可立即恢复。":
        "Deleted tasks go to the Recycle Bin; click Undo or press the undo shortcut within 5 seconds to restore.",
    "周报": "Weekly report",
    "把本周（周一起）每个任务的日志按 紧急 / 普通 / 已完成 汇总成 Markdown 复制到剪贴板。":
        "Copies this week's (from Monday) log entries, grouped Urgent / Normal / Done, as Markdown.",
    "窗口": "Window",
    "拖动空白处移动，拖边缘缩放，双击标题栏铺满屏幕；钉住按钮让窗口常驻最上层；Esc 隐藏到托盘。":
        "Drag empty space to move, drag edges to resize, double-click to fill the screen. Pin keeps it on top; Esc hides it to the tray.",
}
