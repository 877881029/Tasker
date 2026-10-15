from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QRectF, QSize, Qt, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QIcon, QKeyEvent, QKeySequence, QPainter
from PySide6.QtWidgets import (
    QAbstractButton,
    QFrame,
    QPushButton,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from tasker.resources import resource_path
from tasker.safety import backup_tasks, default_backup_dir, list_backups
from tasker.settings import FIXED_KEYS, GLOBAL_FALLBACKS, SHORTCUTS, get_setting, save_setting
from tasker.shell import autostart
from tasker.theme import (
    CARD,
    CHROME,
    COBALT,
    HOVER,
    INK,
    LINE,
    LINE_STRONG,
    MUTED,
    PAPER,
    SELECTED,
    URGENT_DOT,
    ui_font,
)
from tasker.version import RELEASES_URL, app_version

_MOD_KEYS = {Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta, Qt.Key.Key_AltGr}

FEATURES: tuple[tuple[str, str], ...] = (
    ("状态与 DDL", "右键任务或点详情左上角胶囊改状态：普通 / 紧急 / 已完成。紧急任务可设 DDL，列表右侧显示倒计时（如 03d-14h-57m），紧急任务按 DDL 先后排序；不足 24 小时变红，超期显示红底。"),
    ("到点提醒", "截止前 1 小时和超期时各弹一次系统通知，点通知直接打开任务；托盘图标右下角红点显示超期数量。"),
    ("日志", "详情里每条日志带时间戳，最新在上。写入后保存；只读视图里的 http/https 链接可点击，用浏览器打开。"),
    ("快速记录", "按全局快捷键弹出输入框，回车即建任务，不打开详情；以 ! 开头直接设为紧急。"),
    ("搜索", "搜索标题和日志正文；也可输入关键词筛选：紧急、普通、已完成、超期、今天、DDL。"),
    ("摘要视图", "右上角列表按钮切换：简约（只显示标题）或在标题下显示最新一条日志。"),
    ("已完成折叠", "已完成任务收在列表底部「已完成 (N)」，点一下展开；搜索时自动展开。"),
    ("删除与撤销", "删除的任务进入 Windows 回收站；5 秒内点「撤销」或按撤销快捷键可立即恢复。"),
    ("周报", "把本周（周一起）每个任务的日志按 紧急 / 普通 / 已完成 汇总成 Markdown 复制到剪贴板。"),
    ("窗口", "拖动空白处移动，拖边缘缩放，双击标题栏铺满屏幕；钉住按钮让窗口常驻最上层；Esc 隐藏到托盘。"),
)


def display_keys(keys: str) -> str:
    return keys.replace("Meta+", "Win+") if keys else ""


def event_to_keys(event: QKeyEvent) -> str:
    key = event.key()
    if key in _MOD_KEYS or key == Qt.Key.Key_unknown:
        return ""
    mods = event.modifiers()
    parts: list[str] = []
    if mods & Qt.KeyboardModifier.ControlModifier:
        parts.append("Ctrl")
    if mods & Qt.KeyboardModifier.AltModifier:
        parts.append("Alt")
    if mods & Qt.KeyboardModifier.ShiftModifier:
        parts.append("Shift")
    if mods & Qt.KeyboardModifier.MetaModifier:
        parts.append("Win")
    name = QKeySequence(key).toString(QKeySequence.SequenceFormat.PortableText)
    if not name:
        return ""
    parts.append(name)
    return "+".join(parts)


class ToggleSwitch(QAbstractButton):
    W, H = 36, 20

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(self.W, self.H)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def sizeHint(self) -> QSize:
        return QSize(self.W, self.H)

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        on = self.isChecked()
        track = QRectF(0.5, 0.5, self.W - 1, self.H - 1)
        painter.setPen(QColor(COBALT if on else LINE_STRONG))
        painter.setBrush(QColor(COBALT if on else LINE))
        painter.drawRoundedRect(track, self.H / 2, self.H / 2)
        if self.hasFocus():
            painter.setPen(QColor(COBALT))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(track, self.H / 2, self.H / 2)
        knob = self.H - 6
        x = self.W - knob - 3 if on else 3
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(QRectF(x, 3, knob, knob))
        painter.end()


class ShortcutField(QToolButton):
    captured = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("shortcutField")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumWidth(132)
        self.setFixedHeight(28)
        self._keys = ""
        self._placeholder = "未设置"
        self.toggled.connect(self._paint)
        self._paint()

    def set_keys(self, keys: str, placeholder: str = "未设置") -> None:
        self._keys = keys
        self._placeholder = placeholder
        self.setChecked(False)
        self._paint()

    def keys(self) -> str:
        return self._keys

    def _paint(self, *_args) -> None:
        if self.isChecked():
            self.setText("按下新快捷键…")
        else:
            self.setText(display_keys(self._keys) or self._placeholder)
        self.setAccessibleName(f"快捷键 {self.text()}，点按后按下新组合")

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if not self.isChecked():
            super().keyPressEvent(event)
            return
        if event.key() == Qt.Key.Key_Escape and not event.modifiers():
            self.setChecked(False)
            event.accept()
            return
        keys = event_to_keys(event)
        if keys:
            self.setChecked(False)
            self.captured.emit(keys)
        event.accept()

    def focusOutEvent(self, event) -> None:
        self.setChecked(False)
        super().focusOutEvent(event)


def _label(text: str, *, size: int = 13, color: str = INK, weight: int = 400) -> QLabel:
    label = QLabel(text)
    label.setWordWrap(True)
    label.setStyleSheet(
        f"color:{color};font-size:{size}px;font-weight:{weight};background:transparent;"
    )
    return label


class Card(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("settingsCard")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._rows = 0

    def add_row(self, widget: QWidget) -> QWidget:
        if self._rows:
            line = QFrame()
            line.setObjectName("settingsDivider")
            line.setFixedHeight(1)
            self._layout.addWidget(line)
        self._layout.addWidget(widget)
        self._rows += 1
        return widget


class SettingRow(QWidget):
    def __init__(
        self, title: str, desc: str = "", control: QWidget | None = None, *, wrap: bool = True
    ) -> None:
        super().__init__()
        self.setObjectName("settingRow")
        row = QHBoxLayout(self)
        row.setContentsMargins(16, 12, 16, 12)
        row.setSpacing(16)
        text = QVBoxLayout()
        text.setSpacing(2)
        self.title = _label(title, weight=600)
        text.addWidget(self.title)
        self.desc = _label(desc, size=12, color=MUTED)
        self.desc.setWordWrap(wrap)
        if not wrap:
            self.desc.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.desc.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            self.desc.setToolTip(desc)
        self.desc.setVisible(bool(desc))
        text.addWidget(self.desc)
        self.error = _label("", size=12, color=URGENT_DOT)
        self.error.hide()
        text.addWidget(self.error)
        row.addLayout(text, 1)
        self.control = control
        if control is not None:
            row.addWidget(control, 0, Qt.AlignmentFlag.AlignVCenter)

    def show_error(self, message: str) -> None:
        self.error.setText(message)
        self.error.setVisible(bool(message))


class SettingsWindow(QWidget):
    SECTIONS = (("general", "通用"), ("shortcuts", "快捷键"), ("features", "功能说明"), ("data", "数据"))

    def __init__(self, dock, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._dock = dock
        self._root = dock.store_root()
        self.setObjectName("settingsWindow")
        self.setWindowTitle("Tasker 设置")
        self.setWindowFlags(Qt.WindowType.Window)
        icon = resource_path("assets", "icons", "tasker.ico")
        if icon.exists():
            self.setWindowIcon(QIcon(str(icon)))
        self.setFont(ui_font(13))
        self.resize(780, 560)
        self.setMinimumSize(620, 420)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            f"QWidget#settingsWindow{{background:{PAPER};}}"
            f"QWidget#settingsNav{{background:{CHROME};border-right:1px solid {LINE};}}"
            f"QPushButton#navItem{{background:transparent;color:{INK};border:none;"
            "border-radius:6px;padding:7px 12px;font-size:13px;text-align:left;}"
            f"QPushButton#navItem:hover{{background:{HOVER};}}"
            f"QPushButton#navItem:checked{{background:{SELECTED};font-weight:600;}}"
            f"QFrame#settingsCard{{background:{CARD};border:1px solid {LINE};border-radius:8px;}}"
            f"QFrame#settingsDivider{{background:{LINE};border:none;}}"
            "QWidget#settingRow{background:transparent;}"
            f"QScrollArea#settingsScroll{{background:{PAPER};border:none;}}"
            f"QWidget#settingsPage{{background:{PAPER};}}"
            f"QToolButton#shortcutField,QToolButton#settingsAction{{background:{CARD};color:{INK};"
            f"border:1px solid {LINE_STRONG};border-radius:6px;padding:0 12px;font-size:12px;"
            "font-weight:600;}"
            f"QToolButton#shortcutField:hover,QToolButton#settingsAction:hover{{background:{HOVER};}}"
            f"QToolButton#shortcutField:checked{{border:2px solid {COBALT};color:{COBALT};}}"
            f"QToolButton#shortcutField:focus,QToolButton#settingsAction:focus{{border:2px solid {COBALT};}}"
            f"QToolButton#linkAction{{background:transparent;color:{COBALT};border:none;"
            "font-size:12px;font-weight:600;padding:0 4px;}"
            "QToolButton#linkAction:hover{text-decoration:underline;}"
        )
        self.nav_buttons: dict[str, QPushButton] = {}
        self.rows: dict[str, SettingRow] = {}
        self.toggles: dict[str, ToggleSwitch] = {}
        self.shortcut_fields: dict[str, ShortcutField] = {}

        nav = QWidget()
        nav.setObjectName("settingsNav")
        nav.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        nav.setFixedWidth(176)
        nav_box = QVBoxLayout(nav)
        nav_box.setContentsMargins(10, 16, 10, 12)
        nav_box.setSpacing(2)
        heading = _label("设置", size=15, weight=600)
        heading.setContentsMargins(12, 0, 0, 10)
        nav_box.addWidget(heading)
        self.pages = QStackedWidget()
        for key, title in self.SECTIONS:
            button = QPushButton()
            button.setObjectName("navItem")
            button.setText(title)
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            button.clicked.connect(lambda _c=False, k=key: self.show_section(k))
            nav_box.addWidget(button)
            self.nav_buttons[key] = button
            builder: Callable[[], QWidget] = getattr(self, f"_build_{key}")
            self.pages.addWidget(self._page(title, builder()))
        nav_box.addStretch(1)
        nav_box.addWidget(_label(f"版本 {app_version()}", size=12, color=MUTED))

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(nav)
        root.addWidget(self.pages, 1)
        self.show_section("general")

    # ---- layout helpers -------------------------------------------------

    def _page(self, title: str, body: QWidget) -> QWidget:
        page = QWidget()
        page.setObjectName("settingsPage")
        box = QVBoxLayout(page)
        box.setContentsMargins(28, 20, 28, 24)
        box.setSpacing(14)
        box.addWidget(_label(title, size=20, weight=600))
        box.addWidget(body)
        box.addStretch(1)
        scroll = QScrollArea()
        scroll.setObjectName("settingsScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(page)
        return scroll

    def _group(self, *cards: tuple[str, Card]) -> QWidget:
        holder = QWidget()
        holder.setObjectName("settingsPage")
        box = QVBoxLayout(holder)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(8)
        for index, (caption, card) in enumerate(cards):
            if caption:
                label = _label(caption, size=12, color=MUTED, weight=600)
                if index:
                    label.setContentsMargins(0, 10, 0, 0)
                box.addWidget(label)
            box.addWidget(card)
        return holder

    def _toggle_row(self, card: Card, key: str, title: str, desc: str, checked: bool, slot) -> None:
        toggle = ToggleSwitch()
        toggle.setChecked(checked)
        toggle.setAccessibleName(title)
        toggle.toggled.connect(slot)
        self.toggles[key] = toggle
        self.rows[key] = card.add_row(SettingRow(title, desc, toggle))

    def _action(self, text: str, slot, name: str = "settingsAction") -> QToolButton:
        button = QToolButton()
        button.setObjectName(name)
        button.setText(text)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFixedHeight(28)
        button.clicked.connect(slot)
        return button

    # ---- sections -------------------------------------------------------

    def _build_general(self) -> QWidget:
        card = Card()
        self._toggle_row(
            card, "summary", "显示日志摘要",
            "在任务标题下显示最新一条日志；关闭为只显示标题的简约列表。",
            self._dock.summary_mode(), self._dock.set_summary_mode,
        )
        self._toggle_row(
            card, "reminders", "DDL 到点提醒",
            "截止前 1 小时和超期时弹出系统通知。",
            bool(get_setting(self._root, "reminders")), self._set_reminders,
        )
        self._toggle_row(
            card, "autostart", "开机自启",
            "登录 Windows 后自动在托盘启动 Tasker。",
            autostart.is_enabled(), self._set_autostart,
        )
        return self._group(("", card))

    def _build_shortcuts(self) -> QWidget:
        editable = Card()
        mapping = self._dock.shortcut_keys()
        for action, (label, desc, _default, scope) in SHORTCUTS.items():
            field = ShortcutField()
            field.captured.connect(lambda keys, a=action: self._capture(a, keys))
            self.shortcut_fields[action] = field
            suffix = "（全局，在任何程序中都可用）" if scope == "global" else ""
            self.rows[f"key:{action}"] = editable.add_row(SettingRow(label, desc + suffix, field))
            self._paint_field(action, mapping[action])
        reset = SettingRow("恢复默认", "把以上快捷键全部恢复为默认组合。", self._action("恢复默认", self._reset))
        editable.add_row(reset)
        fixed = Card()
        for keys, desc in FIXED_KEYS:
            badge = QLabel(keys)
            badge.setStyleSheet(
                f"color:{INK};background:{PAPER};border:1px solid {LINE};border-radius:6px;"
                "padding:3px 10px;font-size:12px;font-weight:600;"
            )
            fixed.add_row(SettingRow(desc, "", badge))
        hint = _label("点按快捷键后按下新组合；Esc 取消。", size=12, color=MUTED)
        holder = self._group(("可自定义", editable), ("固定按键", fixed))
        holder.layout().insertWidget(0, hint)
        return holder

    def _build_features(self) -> QWidget:
        card = Card()
        for title, desc in FEATURES:
            card.add_row(SettingRow(title, desc))
        return self._group(("", card))

    def _build_data(self) -> QWidget:
        storage = Card()
        self.data_row = storage.add_row(
            SettingRow(
                "数据目录", str(self._root), self._action("打开文件夹", self.open_data_dir), wrap=False
            )
        )
        storage.add_row(
            SettingRow(
                "删除",
                "删除的任务进入 Windows 回收站，可从回收站还原。",
            )
        )
        backup = Card()
        self._toggle_row(
            backup, "auto_backup", "每日自动备份",
            "每天第一次启动时把全部任务打包成 zip，保留最近 7 份。",
            bool(get_setting(self._root, "auto_backup")),
            lambda on: save_setting(self._root, "auto_backup", bool(on)),
        )
        buttons = QWidget()
        line = QHBoxLayout(buttons)
        line.setContentsMargins(0, 0, 0, 0)
        line.setSpacing(8)
        line.addWidget(self._action("立即备份", self.backup_now))
        line.addWidget(self._action("打开备份文件夹", self.open_backup_dir))
        self.backup_row = backup.add_row(
            SettingRow("备份位置", self._backup_desc(), buttons, wrap=False)
        )
        about = Card()
        about.add_row(
            SettingRow(
                "版本", f"Tasker {app_version()}",
                self._action("查看发布版本", self.open_releases, name="linkAction"),
            )
        )
        return self._group(("存储", storage), ("备份", backup), ("关于", about))

    # ---- behaviour ------------------------------------------------------

    def show_section(self, key: str) -> None:
        keys = [k for k, _t in self.SECTIONS]
        self.nav_buttons[key].setChecked(True)
        self.pages.setCurrentIndex(keys.index(key))

    def current_section(self) -> str:
        return self.SECTIONS[self.pages.currentIndex()][0]

    def sync(self) -> None:
        for key, value in (
            ("summary", self._dock.summary_mode()),
            ("reminders", bool(get_setting(self._root, "reminders"))),
            ("autostart", autostart.is_enabled()),
            ("auto_backup", bool(get_setting(self._root, "auto_backup"))),
        ):
            toggle = self.toggles[key]
            toggle.blockSignals(True)
            toggle.setChecked(value)
            toggle.blockSignals(False)
            toggle.update()
        mapping = self._dock.shortcut_keys()
        for action in SHORTCUTS:
            self._paint_field(action, mapping[action])
            self.rows[f"key:{action}"].show_error("")

    def _paint_field(self, action: str, keys: str) -> None:
        field = self.shortcut_fields[action]
        if action == "quick_capture" and not keys:
            active = self._dock.hotkey_label
            auto = " → ".join(GLOBAL_FALLBACKS)
            field.set_keys(active, placeholder="自动")
            field.setToolTip(f"自动：依次尝试 {auto}，当前生效 {active or '无'}")
        else:
            field.set_keys(keys)
            field.setToolTip("")

    def _capture(self, action: str, keys: str) -> None:
        error = self._dock.apply_shortcut(action, keys)
        self.rows[f"key:{action}"].show_error(error or "")
        self._paint_field(action, self._dock.shortcut_keys()[action])

    def _reset(self) -> None:
        self._dock.reset_shortcuts()
        self.sync()

    def _set_reminders(self, on: bool) -> None:
        save_setting(self._root, "reminders", bool(on))

    def _set_autostart(self, on: bool) -> None:
        if not autostart.set_enabled(bool(on)):
            self.rows["autostart"].show_error("写入注册表失败")
            toggle = self.toggles["autostart"]
            toggle.blockSignals(True)
            toggle.setChecked(autostart.is_enabled())
            toggle.blockSignals(False)
        else:
            self.rows["autostart"].show_error("")

    def _backup_desc(self) -> str:
        folder = default_backup_dir()
        backups = list_backups(folder)
        latest = f"\n最近一次 {backups[-1].stem.removeprefix('tasker-')}" if backups else ""
        return f"{folder}{latest}"

    def backup_now(self) -> None:
        path = backup_tasks(self._root, default_backup_dir())
        self.backup_row.desc.setText(self._backup_desc())
        self.backup_row.show_error("")
        self.last_backup = path

    def open_data_dir(self) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._root)))

    def open_backup_dir(self) -> None:
        folder = default_backup_dir()
        folder.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def open_releases(self) -> None:
        QDesktopServices.openUrl(QUrl(RELEASES_URL))

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            event.accept()
            return
        super().keyPressEvent(event)
