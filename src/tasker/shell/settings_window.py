from __future__ import annotations

from PySide6.QtCore import QPoint, QRectF, QSize, Qt, QUrl, Signal
from PySide6.QtGui import (
    QColor,
    QDesktopServices,
    QGuiApplication,
    QIcon,
    QKeyEvent,
    QKeySequence,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import (
    QAbstractButton,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from tasker.i18n import LANGUAGES, language, tr
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
RADIUS = 12
EDGE = 6
CONTENT_MAX = 860

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


def _icon(name: str) -> QIcon:
    path = resource_path("assets", "icons", f"{name}.svg")
    return QIcon(str(path)) if path.exists() else QIcon()


def _label(text: str, *, size: int = 14, color: str = INK, weight: int = 400, wrap: bool = True) -> QLabel:
    label = QLabel(text)
    label.setWordWrap(wrap)
    label.setFont(ui_font(size, weight))
    label.setStyleSheet(f"color:{color};background:transparent;")
    return label


class ToggleSwitch(QAbstractButton):
    W, H = 40, 22

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
        track = QRectF(1, 1, self.W - 2, self.H - 2)
        radius = track.height() / 2
        painter.setPen(QPen(QColor(COBALT if on else LINE_STRONG), 1.2))
        painter.setBrush(QColor(COBALT if on else HOVER))
        painter.drawRoundedRect(track, radius, radius)
        knob = self.H - 8
        x = self.W - knob - 4 if on else 4
        painter.setPen(QPen(QColor(CARD if on else LINE_STRONG), 1))
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(QRectF(x, 4, knob, knob))
        if self.hasFocus():
            painter.setPen(QPen(QColor(COBALT), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(QRectF(0.5, 0.5, self.W - 1, self.H - 1), radius + 1, radius + 1)
        painter.end()


class ShortcutField(QToolButton):
    captured = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("shortcutField")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumWidth(140)
        self.setFixedHeight(30)
        self._keys = ""
        self._placeholder = tr("未设置")
        self.toggled.connect(self._paint)
        self._paint()

    def set_keys(self, keys: str, placeholder: str | None = None) -> None:
        self._keys = keys
        self._placeholder = placeholder or tr("未设置")
        self.setChecked(False)
        self._paint()

    def keys(self) -> str:
        return self._keys

    def _paint(self, *_args) -> None:
        if self.isChecked():
            self.setText(tr("按下新快捷键…"))
        else:
            shown = display_keys(self._keys)
            self.setText(shown.replace("+", " + ") if shown else self._placeholder)
        self.setAccessibleName(tr("快捷键 {keys}，点按后按下新组合", keys=self.text()))

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


class SettingRow(QWidget):
    """Copilot-style row: title, muted description, control on the right. No card chrome."""

    def __init__(
        self, title: str, desc: str = "", control: QWidget | None = None, *, wrap: bool = True
    ) -> None:
        super().__init__()
        self.setObjectName("settingRow")
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 8, 0, 8)
        row.setSpacing(24)
        text = QVBoxLayout()
        text.setSpacing(2)
        self.title = _label(title, size=14)
        text.addWidget(self.title)
        self.desc = _label(desc, size=13, color=MUTED, wrap=wrap)
        if not wrap:
            self.desc.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.desc.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            self.desc.setToolTip(desc)
        self.desc.setVisible(bool(desc))
        text.addWidget(self.desc)
        self.error = _label("", size=13, color=URGENT_DOT)
        self.error.hide()
        text.addWidget(self.error)
        row.addLayout(text, 1)
        self.control = control
        if control is not None:
            row.addWidget(control, 0, Qt.AlignmentFlag.AlignVCenter)
        self.search_text = f"{title} {desc}".casefold()

    def show_error(self, message: str) -> None:
        self.error.setText(message)
        self.error.setVisible(bool(message))


class Section(QWidget):
    """A sub-heading plus its rows; hides itself when a search filters all rows out."""

    def __init__(self, caption: str = "") -> None:
        super().__init__()
        self._box = QVBoxLayout(self)
        self._box.setContentsMargins(0, 0, 0, 0)
        self._box.setSpacing(0)
        self.caption = _label(caption, size=14, weight=600) if caption else None
        if self.caption is not None:
            self.caption.setContentsMargins(0, 0, 0, 4)
            self._box.addWidget(self.caption)
        self.rows: list[SettingRow] = []

    def add_row(self, row: SettingRow) -> SettingRow:
        self._box.addWidget(row)
        self.rows.append(row)
        if self.caption is not None:
            row.search_text += " " + self.caption.text().casefold()
        return row

    def filter(self, needle: str) -> int:
        shown = 0
        for row in self.rows:
            match = not needle or needle in row.search_text
            row.setVisible(match)
            shown += int(match)
        self.setVisible(shown > 0)
        return shown


class Page(QScrollArea):
    def __init__(self, title: str, description: str) -> None:
        super().__init__()
        self.setObjectName("settingsScroll")
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        body.setObjectName("settingsPage")
        outer = QHBoxLayout(body)
        outer.setContentsMargins(28, 4, 28, 28)
        column = QWidget()
        column.setObjectName("settingsPage")
        column.setMaximumWidth(CONTENT_MAX)
        self._box = QVBoxLayout(column)
        self._box.setContentsMargins(0, 0, 0, 0)
        self._box.setSpacing(22)
        self.description = _label(description, size=14, color=MUTED)
        self._box.addWidget(self.description)
        self.empty = _label(tr("没有匹配的设置"), size=14, color=MUTED)
        self.empty.hide()
        self._box.addWidget(self.empty)
        outer.addWidget(column, 1)
        self.title = title
        self.sections: list[Section] = []
        self.setWidget(body)
        for widget in (self, self.viewport(), body, column):
            widget.setAutoFillBackground(False)

    def add_section(self, section: Section) -> Section:
        self._box.insertWidget(self._box.count() - 1, section)
        self.sections.append(section)
        return section

    def add_widget(self, widget: QWidget) -> None:
        self._box.insertWidget(self._box.count() - 1, widget)

    def finish(self) -> None:
        self._box.addStretch(1)

    def filter(self, needle: str) -> int:
        shown = sum(section.filter(needle) for section in self.sections)
        self.description.setVisible(not needle)
        self.empty.setVisible(bool(needle) and shown == 0)
        return shown


class SettingsWindow(QWidget):
    SECTIONS = (
        ("general", "通用", "nav-general", "常用开关和界面语言。"),
        ("shortcuts", "快捷键", "nav-keyboard", "点按快捷键后按下新组合；Esc 取消。"),
        ("features", "功能说明", "nav-features", "Tasker 的主要功能和用法。"),
        ("data", "数据", "nav-data", "数据只保存在本机；删除进入回收站，并每天自动备份。"),
    )

    def __init__(self, dock, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._dock = dock
        self._root = dock.store_root()
        self._drag: QPoint | None = None
        self.setObjectName("settingsWindow")
        self.setWindowTitle(tr("Tasker 设置"))
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        icon = resource_path("assets", "icons", "tasker.ico")
        if icon.exists():
            self.setWindowIcon(QIcon(str(icon)))
        self.setFont(ui_font(14))
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.resize(900, 620)
        self.setMinimumSize(680, 440)
        self.setStyleSheet(self._style())
        self.nav_buttons: dict[str, QPushButton] = {}
        self.rows: dict[str, SettingRow] = {}
        self.toggles: dict[str, ToggleSwitch] = {}
        self.shortcut_fields: dict[str, ShortcutField] = {}
        self.pages_by_key: dict[str, Page] = {}

        nav = QWidget()
        nav.setObjectName("settingsNav")
        nav.setFixedWidth(232)
        nav_box = QVBoxLayout(nav)
        nav_box.setContentsMargins(10, 14, 10, 12)
        nav_box.setSpacing(2)
        brand = QHBoxLayout()
        brand.setContentsMargins(8, 0, 0, 10)
        brand.setSpacing(10)
        logo = QLabel()
        logo.setPixmap(QIcon(str(resource_path("assets", "icons", "tasker.ico"))).pixmap(22, 22))
        brand.addWidget(logo)
        name_box = QVBoxLayout()
        name_box.setSpacing(0)
        name_box.addWidget(_label("Tasker", size=14, weight=600))
        name_box.addWidget(_label(tr("版本 {version}", version=app_version()), size=12, color=MUTED))
        brand.addLayout(name_box, 1)
        nav_box.addLayout(brand)
        self.search = QLineEdit()
        self.search.setObjectName("settingsSearch")
        self.search.setPlaceholderText(tr("搜索设置…"))
        self.search.setClearButtonEnabled(True)
        self.search.addAction(_icon("search"), QLineEdit.ActionPosition.LeadingPosition)
        self.search.setFixedHeight(32)
        self.search.textChanged.connect(self.apply_search)
        nav_box.addWidget(self.search)
        nav_box.addSpacing(10)

        self.pages = QStackedWidget()
        self.pages.setObjectName("settingsStack")
        for key, title, icon_name, description in self.SECTIONS:
            button = QPushButton(tr(title))
            button.setObjectName("navItem")
            button.setIcon(_icon(icon_name))
            button.setIconSize(QSize(16, 16))
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            button.setFixedHeight(34)
            button.clicked.connect(lambda _c=False, k=key: self.show_section(k))
            nav_box.addWidget(button)
            self.nav_buttons[key] = button
            page = Page(tr(title), tr(description))
            getattr(self, f"_build_{key}")(page)
            page.finish()
            self.pages.addWidget(page)
            self.pages_by_key[key] = page
        nav_box.addStretch(1)

        self.header_title = _label("", size=16, weight=600)
        close = QToolButton()
        close.setObjectName("closeSettings")
        close.setIcon(_icon("hide"))
        close.setIconSize(QSize(14, 14))
        close.setFixedSize(30, 30)
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.setAccessibleName(tr("关闭"))
        close.clicked.connect(self.close)
        self.close_btn = close
        header = QWidget()
        header.setObjectName("settingsHeader")
        header_box = QHBoxLayout(header)
        header_box.setContentsMargins(28, 16, 14, 8)
        header_box.addWidget(self.header_title, 1)
        header_box.addWidget(close, 0, Qt.AlignmentFlag.AlignTop)
        self._header = header

        main = QWidget()
        main.setObjectName("settingsMain")
        main_box = QVBoxLayout(main)
        main_box.setContentsMargins(0, 0, 0, 0)
        main_box.setSpacing(0)
        main_box.addWidget(header)
        main_box.addWidget(self.pages, 1)

        root = QHBoxLayout(self)
        root.setContentsMargins(1, 1, 1, 1)
        root.setSpacing(0)
        root.addWidget(nav)
        root.addWidget(main, 1)
        self._nav = nav
        self.show_section("general")

    # ---- look -------------------------------------------------------------

    def _style(self) -> str:
        return (
            "QWidget#settingsNav,QWidget#settingsMain,QWidget#settingsHeader,"
            "QStackedWidget#settingsStack,QScrollArea#settingsScroll,QWidget#settingsPage,"
            "QWidget#settingRow{background:transparent;border:none;}"
            f"QLineEdit#settingsSearch{{background:{CARD};color:{INK};border:1px solid {LINE_STRONG};"
            f"border-radius:6px;padding:0 6px;font-size:13px;selection-background-color:{COBALT};}}"
            f"QLineEdit#settingsSearch:focus{{border:1px solid {COBALT};}}"
            f"QPushButton#navItem{{background:transparent;color:{INK};border:none;border-radius:6px;"
            "padding:0 10px;font-size:14px;text-align:left;}"
            f"QPushButton#navItem:hover{{background:{HOVER};}}"
            f"QPushButton#navItem:checked{{background:{SELECTED};}}"
            f"QToolButton#closeSettings{{background:transparent;border:none;border-radius:6px;}}"
            f"QToolButton#closeSettings:hover{{background:{HOVER};}}"
            f"QToolButton#shortcutField,QToolButton#settingsAction,QPushButton#langOption{{"
            f"background:{CARD};color:{INK};border:1px solid {LINE_STRONG};border-radius:6px;"
            "padding:0 12px;font-size:13px;}"
            f"QToolButton#shortcutField:hover,QToolButton#settingsAction:hover,"
            f"QPushButton#langOption:hover{{background:{HOVER};}}"
            f"QToolButton#shortcutField:checked{{border:1px solid {COBALT};color:{COBALT};}}"
            f"QToolButton#shortcutField:focus,QToolButton#settingsAction:focus{{border:1px solid {COBALT};}}"
            f"QPushButton#langOption:checked{{background:{SELECTED};font-weight:600;}}"
            f"QToolButton#linkAction{{background:transparent;color:{COBALT};border:none;"
            "font-size:13px;padding:0 4px;}"
            "QToolButton#linkAction:hover{text-decoration:underline;}"
            f"QLabel#keycap{{color:{INK};background:{CARD};border:1px solid {LINE_STRONG};"
            "border-bottom-width:2px;border-radius:5px;padding:2px 8px;font-size:12px;}"
            "QScrollBar:vertical{background:transparent;width:10px;margin:4px 2px;}"
            f"QScrollBar::handle:vertical{{background:{LINE_STRONG};border-radius:3px;min-height:32px;}}"
            "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}"
            "QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical{background:none;}"
        )

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        outline = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        path.addRoundedRect(outline, RADIUS, RADIUS)
        painter.fillPath(path, QColor(PAPER))
        painter.save()
        painter.setClipPath(path)
        nav_width = self._nav.width() + 1
        painter.fillRect(QRectF(0, 0, nav_width, self.height()), QColor(CHROME))
        painter.setPen(QPen(QColor(LINE), 1))
        painter.drawLine(QPoint(nav_width, 0), QPoint(nav_width, self.height()))
        painter.restore()
        painter.setPen(QPen(QColor(LINE_STRONG), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)
        painter.end()

    # ---- builders ---------------------------------------------------------

    def _toggle_row(self, section: Section, key: str, title: str, desc: str, checked: bool, slot) -> None:
        toggle = ToggleSwitch()
        toggle.setChecked(checked)
        toggle.setAccessibleName(title)
        toggle.toggled.connect(slot)
        self.toggles[key] = toggle
        self.rows[key] = section.add_row(SettingRow(title, desc, toggle))

    def _action(self, text: str, slot, name: str = "settingsAction") -> QToolButton:
        button = QToolButton()
        button.setObjectName(name)
        button.setText(text)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFixedHeight(30)
        button.clicked.connect(slot)
        return button

    def _build_general(self, page: Page) -> None:
        ui = page.add_section(Section(tr("界面")))
        switch = QWidget()
        line = QHBoxLayout(switch)
        line.setContentsMargins(0, 0, 0, 0)
        line.setSpacing(6)
        self.language_buttons: dict[str, QPushButton] = {}
        for code, label in LANGUAGES:
            option = QPushButton(label)
            option.setObjectName("langOption")
            option.setCheckable(True)
            option.setAutoExclusive(True)
            option.setFixedHeight(30)
            option.setCursor(Qt.CursorShape.PointingHandCursor)
            option.setChecked(code == str(get_setting(self._root, "language")))
            option.clicked.connect(lambda _c=False, c=code: self.set_language(c))
            line.addWidget(option)
            self.language_buttons[code] = option
        self.rows["language"] = ui.add_row(
            SettingRow(tr("语言"), tr("界面语言。切换后需要重启 Tasker。"), switch)
        )
        self.restart_row = ui.add_row(
            SettingRow(tr("切换后需要重启 Tasker 才能生效。"), "", self._action(tr("立即重启"), self.restart))
        )
        self.restart_row.hide()
        self._toggle_row(
            ui, "summary", tr("显示日志摘要"),
            tr("在任务标题下显示最新一条日志；关闭为只显示标题的简约列表。"),
            self._dock.summary_mode(), self._dock.set_summary_mode,
        )
        startup = page.add_section(Section(tr("提醒与启动")))
        self._toggle_row(
            startup, "reminders", tr("DDL 到点提醒"),
            tr("截止前 1 小时和超期时弹出系统通知。"),
            bool(get_setting(self._root, "reminders")), self._set_reminders,
        )
        self._toggle_row(
            startup, "autostart", tr("开机自启"),
            tr("登录 Windows 后自动在托盘启动 Tasker。"),
            autostart.is_enabled(), self._set_autostart,
        )

    def _build_shortcuts(self, page: Page) -> None:
        editable = page.add_section(Section(tr("可自定义")))
        mapping = self._dock.shortcut_keys()
        for action, (label, desc, _default, scope) in SHORTCUTS.items():
            field = ShortcutField()
            field.captured.connect(lambda keys, a=action: self._capture(a, keys))
            self.shortcut_fields[action] = field
            suffix = tr("（全局，在任何程序中都可用）") if scope == "global" else ""
            self.rows[f"key:{action}"] = editable.add_row(SettingRow(tr(label), tr(desc) + suffix, field))
            self._paint_field(action, mapping[action])
        editable.add_row(
            SettingRow(tr("恢复默认"), tr("把以上快捷键全部恢复为默认组合。"), self._action(tr("恢复默认"), self._reset))
        )
        fixed = page.add_section(Section(tr("固定按键")))
        for keys, desc in FIXED_KEYS:
            cap = QLabel(tr(keys))
            cap.setObjectName("keycap")
            fixed.add_row(SettingRow(tr(desc), "", cap))

    def _build_features(self, page: Page) -> None:
        section = page.add_section(Section())
        for title, desc in FEATURES:
            section.add_row(SettingRow(tr(title), tr(desc)))

    def _build_data(self, page: Page) -> None:
        storage = page.add_section(Section(tr("存储")))
        self.data_row = storage.add_row(
            SettingRow(tr("数据目录"), str(self._root), self._action(tr("打开文件夹"), self.open_data_dir), wrap=False)
        )
        storage.add_row(SettingRow(tr("删除"), tr("删除的任务进入 Windows 回收站，可从回收站还原。")))
        backup = page.add_section(Section(tr("备份")))
        self._toggle_row(
            backup, "auto_backup", tr("每日自动备份"),
            tr("每天第一次启动时把全部任务打包成 zip，保留最近 7 份。"),
            bool(get_setting(self._root, "auto_backup")),
            lambda on: save_setting(self._root, "auto_backup", bool(on)),
        )
        buttons = QWidget()
        line = QHBoxLayout(buttons)
        line.setContentsMargins(0, 0, 0, 0)
        line.setSpacing(8)
        line.addWidget(self._action(tr("立即备份"), self.backup_now))
        line.addWidget(self._action(tr("打开备份文件夹"), self.open_backup_dir))
        self.backup_row = backup.add_row(SettingRow(tr("备份位置"), self._backup_desc(), buttons, wrap=False))
        about = page.add_section(Section(tr("关于")))
        about.add_row(
            SettingRow(
                tr("版本"), f"Tasker {app_version()}",
                self._action(tr("查看发布版本"), self.open_releases, name="linkAction"),
            )
        )

    # ---- behaviour --------------------------------------------------------

    def show_section(self, key: str) -> None:
        self.nav_buttons[key].setChecked(True)
        page = self.pages_by_key[key]
        self.pages.setCurrentWidget(page)
        self.header_title.setText(page.title)

    def current_section(self) -> str:
        current = self.pages.currentWidget()
        return next(key for key, page in self.pages_by_key.items() if page is current)

    def apply_search(self, text: str) -> None:
        needle = text.strip().casefold()
        first = None
        for key, page in self.pages_by_key.items():
            shown = page.filter(needle)
            self.nav_buttons[key].setVisible(not needle or shown > 0)
            if shown and first is None:
                first = key
        if needle and first is not None and not self.nav_buttons[self.current_section()].isVisible():
            self.show_section(first)
        elif needle and first is None:
            self.pages.currentWidget().filter(needle)

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
            field.set_keys(active, placeholder=tr("自动"))
            field.setToolTip(
                tr("自动：依次尝试 {auto}，当前生效 {active}", auto=" → ".join(GLOBAL_FALLBACKS), active=active or tr("无"))
            )
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

    def set_language(self, code: str) -> None:
        save_setting(self._root, "language", code)
        self.restart_row.setVisible(code != language())

    def restart(self) -> None:
        self._dock.restart_app()

    def _set_reminders(self, on: bool) -> None:
        save_setting(self._root, "reminders", bool(on))

    def _set_autostart(self, on: bool) -> None:
        if not autostart.set_enabled(bool(on)):
            self.rows["autostart"].show_error(tr("写入注册表失败"))
            toggle = self.toggles["autostart"]
            toggle.blockSignals(True)
            toggle.setChecked(autostart.is_enabled())
            toggle.blockSignals(False)
        else:
            self.rows["autostart"].show_error("")

    def _backup_desc(self) -> str:
        folder = default_backup_dir()
        backups = list_backups(folder)
        if not backups:
            return str(folder)
        stamp = backups[-1].stem.removeprefix("tasker-")
        return f"{folder}\n{tr('最近一次 {stamp}', stamp=stamp)}"

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

    def center_on(self, widget: QWidget) -> None:
        screen = QGuiApplication.screenAt(widget.frameGeometry().center()) or QGuiApplication.primaryScreen()
        avail = screen.availableGeometry()
        width = min(self.width(), avail.width() - 40)
        height = min(self.height(), avail.height() - 40)
        self.resize(width, height)
        self.move(avail.x() + (avail.width() - width) // 2, avail.y() + (avail.height() - height) // 2)

    # ---- frameless move / resize -----------------------------------------

    def _edges(self, pos: QPoint) -> Qt.Edges:
        edges = Qt.Edges()
        if pos.x() <= EDGE:
            edges |= Qt.Edge.LeftEdge
        if pos.x() >= self.width() - EDGE:
            edges |= Qt.Edge.RightEdge
        if pos.y() <= EDGE:
            edges |= Qt.Edge.TopEdge
        if pos.y() >= self.height() - EDGE:
            edges |= Qt.Edge.BottomEdge
        return edges

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.windowHandle() is not None:
            pos = event.position().toPoint()
            edges = self._edges(pos)
            if edges and self.windowHandle().startSystemResize(edges):
                event.accept()
                return
            child = self.childAt(pos)
            if child is None or child in (self._header, self.header_title, self._nav) or (
                child.objectName() in {"settingsHeader", "settingsNav"}
            ):
                if self.windowHandle().startSystemMove():
                    event.accept()
                    return
        super().mousePressEvent(event)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        # Keep the search box unfocused on open, like Copilot; Ctrl+F focuses it.
        self.setFocus(Qt.FocusReason.OtherFocusReason)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            if self.search.hasFocus() and self.search.text():
                self.search.clear()
            else:
                self.close()
            event.accept()
            return
        if event.matches(QKeySequence.StandardKey.Find):
            self.search.setFocus()
            self.search.selectAll()
            event.accept()
            return
        super().keyPressEvent(event)
