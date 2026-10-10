from __future__ import annotations

import ctypes
import os
from ctypes import wintypes

from PySide6.QtCore import QEvent, QPoint, QRect, QRectF, QSize, Qt
from PySide6.QtGui import (
    QColor,
    QGuiApplication,
    QIcon,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPalette,
    QPen,
    QRegion,
)
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QScrollArea,
    QSizePolicy,
    QSystemTrayIcon,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from tasker.resources import resource_path
from tasker.shell.detail import DetailWindow
from tasker.shell.status import apply_status, build_status_menu, style_menu
from tasker.store import Item, Store
from tasker.theme import (
    CARD,
    CHROME,
    COBALT,
    HOVER,
    INK,
    LINE,
    LINE_STRONG,
    MUTED,
    SHELL_RADIUS,
    STATE_DOT,
    STATE_LABEL,
    card_style,
    dock_style,
    ui_font,
)


def geometry_for_screen(avail: QRect) -> QRect:
    width = max(320, avail.width() // 3)
    x = avail.x() + avail.width() - width
    return QRect(x, avail.y(), width, avail.height())


def default_extra_width(collapsed: QRect) -> int:
    return max(0, collapsed.width() * 2)


def expand_from_dock(collapsed: QRect, extra_width: int, avail: QRect) -> QRect:
    extra = max(int(extra_width), 0)
    room = collapsed.x() - avail.x()
    extra = min(extra, max(room, 0))
    return QRect(
        collapsed.x() - extra,
        collapsed.y(),
        collapsed.width() + extra,
        collapsed.height(),
    )


FRAME_MARGIN = 8
HTCLIENT = 1
HTLEFT = 10
HTRIGHT = 11
HTTOP = 12
HTTOPLEFT = 13
HTTOPRIGHT = 14
HTBOTTOM = 15
HTBOTTOMLEFT = 16
HTBOTTOMRIGHT = 17
WM_NCHITTEST = 0x0084
WM_NCCALCSIZE = 0x0083
MOVE_NAMES = frozenset(
    {"shell", "dock", "chrome", "listHost", "listScroll", "detailHost", "notch"}
)
IGNORE_NAMES = frozenset(
    {
        "search",
        "addBtn",
        "pinBtn",
        "closeDock",
        "itemCard",
        "titleField",
        "journalEditor",
        "journalDocument",
        "doneBox",
        "importance",
        "deleteBtn",
        "statusPill",
        "detailTitle",
    }
)


def edge_hit(pos: QPoint, size: QSize, margin: int = FRAME_MARGIN) -> Qt.Edges:
    edges = Qt.Edges()
    if pos.x() <= margin:
        edges |= Qt.Edge.LeftEdge
    if pos.x() >= size.width() - 1 - margin:
        edges |= Qt.Edge.RightEdge
    if pos.y() <= margin:
        edges |= Qt.Edge.TopEdge
    if pos.y() >= size.height() - 1 - margin:
        edges |= Qt.Edge.BottomEdge
    return edges


def paper_action(
    pos: QPoint, size: QSize, object_name: str, margin: int = FRAME_MARGIN
) -> str:
    if edge_hit(pos, size, margin):
        return "resize"
    name = object_name or ""
    if name in IGNORE_NAMES:
        return "ignore"
    if name in MOVE_NAMES:
        return "move"
    return "ignore"


def paper_corner_radius(geo: QRect, avail: QRect, slack: int = 2) -> int:
    if (
        abs(geo.x() - avail.x()) <= slack
        and abs(geo.y() - avail.y()) <= slack
        and abs(geo.width() - avail.width()) <= slack
        and abs(geo.height() - avail.height()) <= slack
    ):
        return 0
    return SHELL_RADIUS


def round_window_mask(rect: QRect, radius: int) -> QRegion | None:
    if radius <= 0:
        return None
    path = QPainterPath()
    path.addRoundedRect(QRectF(rect), float(radius), float(radius))
    return QRegion(path.toFillPolygon().toPolygon())


class SearchLineEdit(QLineEdit):
    RADIUS = 8

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor(CARD))
        self.setPalette(palette)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(CARD))
        painter.drawRoundedRect(
            QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5),
            self.RADIUS,
            self.RADIUS,
        )
        painter.end()
        super().paintEvent(event)
        if self.hasFocus():
            color, width = COBALT, 2.0
        elif self.underMouse():
            color, width = MUTED, 1.0
        else:
            color, width = LINE_STRONG, 1.0
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        surface_rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Multiply)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(CARD))
        painter.drawRoundedRect(surface_rect, self.RADIUS, self.RADIUS)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        corners = QPainterPath()
        corners.setFillRule(Qt.FillRule.OddEvenFill)
        corners.addRect(QRectF(self.rect()))
        corners.addRoundedRect(surface_rect, self.RADIUS, self.RADIUS)
        painter.fillPath(corners, QColor(CHROME))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(color), width))
        inset = width / 2
        painter.drawRoundedRect(
            QRectF(self.rect()).adjusted(inset, inset, -inset, -inset),
            self.RADIUS,
            self.RADIUS,
        )


def hit_test_local(size: QSize, local: QPoint, margin: int = FRAME_MARGIN) -> int:
    left = local.x() <= margin
    right = local.x() >= size.width() - 1 - margin
    top = local.y() <= margin
    bottom = local.y() >= size.height() - 1 - margin
    if top and left:
        return HTTOPLEFT
    if top and right:
        return HTTOPRIGHT
    if bottom and left:
        return HTBOTTOMLEFT
    if bottom and right:
        return HTBOTTOMRIGHT
    if left:
        return HTLEFT
    if right:
        return HTRIGHT
    if top:
        return HTTOP
    if bottom:
        return HTBOTTOM
    return HTCLIENT


def _lparam_to_local(window: QWidget, x: int, y: int) -> QPoint:
    hwnd = int(window.winId())
    point = wintypes.POINT(int(x), int(y))
    ctypes.windll.user32.ScreenToClient(hwnd, ctypes.byref(point))
    dpr = float(window.devicePixelRatioF()) or 1.0
    return QPoint(round(point.x / dpr), round(point.y / dpr))


class ItemCard(QWidget):
    DOT = 10

    def __init__(
        self, store: Store, item: Item, on_open, on_status=None, parent=None
    ) -> None:
        super().__init__(parent)
        self._store = store
        self.item_id = item.id
        self._on_open = on_open
        self._on_status = on_status
        self._state = item.state
        self.setObjectName("itemCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self.setMinimumHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_status_menu)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)
        self.importance = QToolButton()
        self.importance.setObjectName("importance")
        self.importance.setFixedSize(self.DOT, self.DOT)
        self.importance.setAutoRaise(True)
        self.importance.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.importance.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.title = QLabel()
        self.title.setObjectName("titleField")
        self.title.setWordWrap(True)
        self.title.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        dot_box = QVBoxLayout()
        dot_box.setContentsMargins(0, 5, 0, 0)
        dot_box.setSpacing(0)
        dot_box.addWidget(self.importance)
        dot_box.addStretch(1)
        layout.addLayout(dot_box)
        layout.addWidget(self.title, 1)
        self._selected = False
        self.apply_item(item)

    def is_selected(self) -> bool:
        return self._selected

    def set_selected(self, selected: bool) -> None:
        if selected == self._selected:
            return
        self._selected = selected
        self._paint_surface()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._on_open(self.item_id)
            event.accept()
            return
        super().mousePressEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in {Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space}:
            self._on_open(self.item_id)
            event.accept()
            return
        if event.key() == Qt.Key.Key_Menu:
            self._show_status_menu(QPoint(12, self.height() // 2))
            event.accept()
            return
        super().keyPressEvent(event)

    def status_menu(self) -> QMenu:
        return build_status_menu(self._state, self._pick_status, self)

    def _show_status_menu(self, pos: QPoint) -> None:
        self.status_menu().exec(self.mapToGlobal(pos))

    def _pick_status(self, state: str) -> None:
        item = apply_status(self._store, self.item_id, state)
        self.apply_item(item)
        if self._on_status is not None:
            self._on_status(self.item_id)

    def _paint_surface(self) -> None:
        hover = "" if self._selected else f"QWidget#itemCard:hover{{background:{HOVER};}}"
        self.setStyleSheet(
            f"QWidget#itemCard{{{card_style(self._state, self._selected)}}}"
            f"{hover}"
            f"QWidget#itemCard:focus{{border:2px solid {COBALT};}}"
        )

    def apply_item(self, item: Item) -> None:
        self._state = item.state
        self._paint_surface()
        radius = self.DOT // 2
        self.importance.setStyleSheet(
            f"QToolButton{{background:{STATE_DOT[item.state]};border:none;"
            f"border-radius:{radius}px;}}"
        )
        text = item.title.strip()
        self.title.setText(text or "标题")
        color = INK if text and item.state != "done" else MUTED
        self.title.setStyleSheet(f"color:{color};font-size:14px;")
        state = STATE_LABEL[item.state]
        name = text or "无标题"
        self.setAccessibleName(f"{state}任务：{name}")
        self.setAccessibleDescription("按 Enter 或空格打开详情，菜单键或右键改状态")
        self.setToolTip(f"{state} · {name} · 右键改状态")
        self.importance.setAccessibleName(f"任务状态：{state}")


class ChromeBar(QWidget):
    def __init__(self, host: QWidget, parent=None) -> None:
        super().__init__(parent)
        self._host = host
        self._drag: QPoint | None = None

    def eventFilter(self, watched, event) -> bool:
        if isinstance(event, QMouseEvent):
            self._handle_mouse(event)
        return super().eventFilter(watched, event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self._handle_mouse(event)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        self._handle_mouse(event)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._handle_mouse(event)
        super().mouseReleaseEvent(event)

    def _handle_mouse(self, event: QMouseEvent) -> None:
        kind = event.type()
        if kind == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            self._drag = event.globalPosition().toPoint() - self._host.frameGeometry().topLeft()
        elif kind == QEvent.Type.MouseMove and self._drag is not None:
            if event.buttons() & Qt.MouseButton.LeftButton:
                self._host.move(event.globalPosition().toPoint() - self._drag)
        elif kind == QEvent.Type.MouseButtonRelease:
            self._drag = None


class DockWindow(QWidget):
    def __init__(self, store: Store, parent=None) -> None:
        super().__init__(parent)
        self._store = store
        self._detail: DetailWindow | None = None
        self._open_item_id: str | None = None
        self._collapsed_geo: QRect | None = None
        self._extra_width: int | None = None
        self._active_draft_id: str | None = None
        self.setWindowTitle("Tasker")
        self.setObjectName("dock")
        self.setWindowFlags(self._frame_flags(False))
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        ico = resource_path("assets", "icons", "tasker.ico")
        if ico.exists():
            self.setWindowIcon(QIcon(str(ico)))
        self.setFont(ui_font(13))
        self.setStyleSheet(dock_style())
        self.chrome = ChromeBar(self)
        header = QHBoxLayout(self.chrome)
        header.setContentsMargins(12, 10, 10, 8)
        header.setSpacing(4)
        self.search = SearchLineEdit()
        self.search.setObjectName("search")
        self.search.setFrame(False)
        self.search.setPlaceholderText("查找…")
        self.search.setAccessibleName("搜索事项")
        self.search.setFixedHeight(34)
        search_icon = resource_path("assets", "icons", "search.svg")
        if search_icon.exists():
            self.search.addAction(
                QIcon(str(search_icon)), QLineEdit.ActionPosition.LeadingPosition
            )
        search_palette = self.search.palette()
        search_palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(MUTED))
        self.search.setPalette(search_palette)
        self.search.textChanged.connect(self.refresh)
        self.add_btn = QToolButton()
        self.add_btn.setObjectName("addBtn")
        add_icon = resource_path("assets", "icons", "add.svg")
        if add_icon.exists():
            self.add_btn.setIcon(QIcon(str(add_icon)))
            self.add_btn.setIconSize(QSize(16, 16))
        self.add_btn.setFixedSize(32, 32)
        self.add_btn.setToolTip("新建事项")
        self.add_btn.setAccessibleName("新建事项")
        self.add_btn.clicked.connect(self._add)
        self.pin_btn = QToolButton()
        self.pin_btn.setObjectName("pinBtn")
        self.pin_btn.setText("")
        pin_icon = resource_path("assets", "icons", "pin.svg")
        if pin_icon.exists():
            self.pin_btn.setIcon(QIcon(str(pin_icon)))
            self.pin_btn.setIconSize(QSize(16, 16))
        self.pin_btn.setFixedSize(32, 32)
        self.pin_btn.setToolTip("钉在其它窗口上面")
        self.pin_btn.setAccessibleName("置顶窗口")
        self.pin_btn.setCheckable(True)
        self.pin_btn.toggled.connect(self._toggle_pin)
        self.close_btn = QToolButton()
        self.close_btn.setObjectName("closeDock")
        hide_icon = resource_path("assets", "icons", "hide.svg")
        if hide_icon.exists():
            self.close_btn.setIcon(QIcon(str(hide_icon)))
            self.close_btn.setIconSize(QSize(16, 16))
        self.close_btn.setFixedSize(32, 32)
        self.close_btn.setToolTip("隐藏到托盘")
        self.close_btn.setAccessibleName("隐藏到托盘")
        self.close_btn.clicked.connect(self._close_dock)
        header.addWidget(self.search, 1)
        header.addSpacing(4)
        header.addWidget(self.add_btn)
        header.addWidget(self.pin_btn)
        header.addWidget(self.close_btn)
        QWidget.setTabOrder(self.search, self.add_btn)
        QWidget.setTabOrder(self.add_btn, self.pin_btn)
        QWidget.setTabOrder(self.pin_btn, self.close_btn)

        self.list_host = QWidget()
        self.list_host.setObjectName("listHost")
        self.list_layout = QVBoxLayout(self.list_host)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.list_layout.setContentsMargins(8, 2, 8, 10)
        self.list_layout.setSpacing(2)
        scroll = QScrollArea()
        self.list_scroll = scroll
        scroll.setObjectName("listScroll")
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.list_host)
        scroll.setFrameShape(scroll.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        rail_fill = QColor(CHROME)
        for widget in (scroll, scroll.viewport(), self.list_host):
            palette = widget.palette()
            palette.setColor(QPalette.ColorRole.Window, rail_fill)
            palette.setColor(QPalette.ColorRole.Base, rail_fill)
            widget.setPalette(palette)
            widget.setAutoFillBackground(True)
        self.setAutoFillBackground(False)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.shell = QWidget()
        self.shell.setObjectName("shell")
        self.shell.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        shell_layout = QVBoxLayout(self.shell)
        shell_layout.setContentsMargins(1, 1, 1, 1)
        shell_layout.setSpacing(0)
        self.rail = QWidget()
        self.rail.setObjectName("rail")
        self.rail.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        rail_layout = QVBoxLayout(self.rail)
        rail_layout.setContentsMargins(0, 0, 0, 0)
        rail_layout.setSpacing(0)
        rail_layout.addWidget(self.chrome)
        rail_layout.addWidget(scroll, 1)

        self.detail_host = QWidget()
        self.detail_host.setObjectName("detailHost")
        self.detail_host.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._detail_box = QVBoxLayout(self.detail_host)
        self._detail_box.setContentsMargins(0, 0, 0, 0)
        self._detail_box.setSpacing(0)
        self.detail_host.hide()
        self.detail_host.setMaximumWidth(0)

        self.notch = QWidget()
        self.notch.setObjectName("notch")
        self.notch.setFixedWidth(1)
        self.notch.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.notch.setStyleSheet(f"background:{LINE};")
        self.notch.hide()

        columns = QHBoxLayout()
        columns.setContentsMargins(0, 0, 0, 0)
        columns.setSpacing(0)
        columns.addWidget(self.detail_host, 1)
        columns.addWidget(self.notch, 0)
        columns.addWidget(self.rail, 0)
        shell_layout.addLayout(columns, 1)
        root.addWidget(self.shell)
        self._store.collapse_blank_drafts()
        self._place(initial=True)
        self.refresh()
        self._icon_path = resource_path("assets", "icons", "tasker.ico")
        self._setup_tray()
        self._arm_frame()

    def _frame_flags(self, pinned: bool) -> Qt.WindowType:
        flags = Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint
        if pinned:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        return flags

    def _setup_tray(self) -> None:
        self.tray = QSystemTrayIcon(self)
        if self._icon_path.exists():
            self.tray.setIcon(QIcon(str(self._icon_path)))
        self.tray.setToolTip("Tasker")
        menu = style_menu(QMenu())
        menu.setObjectName("trayMenu")
        show_action = menu.addAction("显示")
        show_action.triggered.connect(self.show_from_tray)
        quit_action = menu.addAction("退出")
        quit_action.triggered.connect(self._quit_app)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_activated)
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()

    def show_from_tray(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()

    def _tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in {
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        }:
            self.show_from_tray()

    def _quit_app(self) -> None:
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._apply_round_mask()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._apply_round_mask()
        self._capture_expanded_layout()

    def moveEvent(self, event) -> None:
        super().moveEvent(event)
        self._capture_expanded_layout()

    def _capture_expanded_layout(self) -> None:
        if not self.detail_host.isVisible():
            return
        rail_w = self.rail.width()
        if rail_w <= 0:
            return
        self._extra_width = max(0, self.width() - rail_w)
        self._collapsed_geo = QRect(
            self.x() + self.width() - rail_w,
            self.y(),
            rail_w,
            self.height(),
        )

    def _apply_round_mask(self) -> None:
        screen = QGuiApplication.primaryScreen()
        avail = screen.availableGeometry() if screen else QRect(self.geometry())
        radius = paper_corner_radius(self.geometry(), avail)
        self.shell.setProperty("flush", "true" if radius == 0 else "false")
        self.shell.style().unpolish(self.shell)
        self.shell.style().polish(self.shell)
        region = round_window_mask(self.rect(), radius)
        if region is None:
            self.clearMask()
        else:
            self.setMask(region)

    def nativeEvent(self, eventType, message):  # noqa: N802
        if os.name == "nt" and eventType in (b"windows_generic_MSG", "windows_generic_MSG"):
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == WM_NCHITTEST:
                x = ctypes.c_int16(msg.lParam & 0xFFFF).value
                y = ctypes.c_int16((msg.lParam >> 16) & 0xFFFF).value
                local = _lparam_to_local(self, x, y)
                return True, hit_test_local(self.size(), local)
            if msg.message == WM_NCCALCSIZE and msg.wParam:
                return True, 0
        return super().nativeEvent(eventType, message)

    def _arm_frame(self) -> None:
        self.setMinimumSize(320, 200)
        self.setMouseTracking(True)
        self.installEventFilter(self)
        for child in self.findChildren(QWidget):
            child.setMouseTracking(True)
            child.installEventFilter(self)

    def eventFilter(self, watched, event) -> bool:
        if (
            isinstance(event, QMouseEvent)
            and event.type() == QEvent.Type.MouseButtonPress
            and event.button() == Qt.MouseButton.LeftButton
            and self._begin_frame_interaction(event)
        ):
            return True
        return super().eventFilter(watched, event)

    def _named_widget_at(self, local: QPoint) -> str:
        widget = self.childAt(local)
        while widget is not None:
            name = widget.objectName()
            if name:
                return str(name)
            widget = widget.parentWidget()
        return str(self.objectName())

    def _begin_frame_interaction(self, event: QMouseEvent) -> bool:
        local = self.mapFromGlobal(event.globalPosition().toPoint())
        name = self._named_widget_at(local)
        action = paper_action(local, self.size(), name)
        handle = self.windowHandle()
        if handle is None:
            return False
        if action == "resize":
            return bool(handle.startSystemResize(edge_hit(local, self.size())))
        if action == "move":
            return bool(handle.startSystemMove())
        return False

    def _place(self, *, initial: bool = False) -> None:
        screen = QGuiApplication.primaryScreen()
        avail = screen.availableGeometry() if screen else QRect(0, 0, 1920, 1080)
        if self.detail_host.isVisible():
            collapsed = self._collapsed_geo or QRect(self.geometry())
            extra = (
                self._extra_width
                if self._extra_width is not None
                else default_extra_width(collapsed)
            )
            self.rail.setFixedWidth(collapsed.width())
            self.setGeometry(expand_from_dock(collapsed, extra, avail))
            return
        self.rail.setMinimumWidth(0)
        self.rail.setMaximumWidth(16777215)
        self.setMinimumSize(320, 200)
        self.setMaximumWidth(16777215)
        if self._collapsed_geo is not None:
            self.setGeometry(self._collapsed_geo)
            self._collapsed_geo = None
            return
        if initial or self.width() < 2:
            target = geometry_for_screen(avail)
            self.setGeometry(target)
            self.resize(target.size())

    def _toggle_pin(self, pinned: bool) -> None:
        self.setWindowFlags(self._frame_flags(pinned))
        self.show()

    def _close_dock(self) -> None:
        if self._detail is not None and self._detail.isVisible():
            self._detail.close_detail()
        self.hide()

    def _add(self) -> None:
        item = self._store.ensure_draft()
        self._active_draft_id = item.id
        self.refresh()
        self.open_detail(item.id)

    def refresh(self) -> None:
        bar = self.list_scroll.verticalScrollBar()
        offset = bar.value()
        self._rebuild_list()
        bar.setValue(offset)

    def cards(self) -> list[ItemCard]:
        found: list[ItemCard] = []
        for index in range(self.list_layout.count()):
            widget = self.list_layout.itemAt(index).widget()
            if isinstance(widget, ItemCard):
                found.append(widget)
        return found

    def _sync_selection(self) -> None:
        for card in self.cards():
            card.set_selected(card.item_id == self._open_item_id)

    def _on_card_status(self, item_id: str) -> None:
        if self._detail is not None and self._detail.isVisible() and item_id == self._open_item_id:
            item = self._store.get(item_id)
            if item is not None:
                self._detail.sync_status(item)
        self.refresh()

    def _on_item_changed(self, _item_id: str) -> None:
        self.refresh()

    def _rebuild_list(self) -> None:
        query = self.search.text()
        while self.list_layout.count():
            child = self.list_layout.takeAt(0)
            widget = child.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        items = self._store.list_visible(query)
        if not items:
            empty = QLabel()
            empty.setObjectName("emptyState")
            empty.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            empty.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
            empty.setWordWrap(True)
            if query.strip():
                empty.setText("没有找到匹配事项\n换个关键词试试")
                empty.setAccessibleName("没有找到匹配事项")
            else:
                empty.setText("还没有事项\n点 + 开始记录")
                empty.setAccessibleName("还没有事项")
            self.list_layout.addWidget(empty)
            self._arm_frame()
            return
        previous: QWidget = self.close_btn
        for item in items:
            card = ItemCard(self._store, item, self.open_detail, self._on_card_status)
            card.set_selected(item.id == self._open_item_id)
            self.list_layout.addWidget(card)
            QWidget.setTabOrder(previous, card)
            previous = card
        self._arm_frame()

    def open_detail(self, item_id: str) -> None:
        item = self._store.get(item_id)
        if item is None:
            return
        if not self.detail_host.isVisible():
            self._collapsed_geo = QRect(self.geometry())
        self._open_item_id = item_id
        if self._detail is None:
            self._detail = DetailWindow(self._store, parent=self.detail_host)
            self._detail.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )
            self._detail_box.addWidget(self._detail, 1)
            self._detail.closed.connect(self._on_detail_closed)
            self._detail.changed.connect(self._on_item_changed)
        self._detail.load(item)
        self.detail_host.setMaximumWidth(16777215)
        self.notch.show()
        self.detail_host.show()
        self._set_bubble(True)
        self._place()
        self._sync_selection()
        self.show()
        self._detail.show()

    def _on_detail_closed(self) -> None:
        self._open_item_id = None
        self.detail_host.hide()
        self.notch.hide()
        self.detail_host.setMaximumWidth(0)
        self._set_bubble(False)
        self._place()
        self.refresh()

    def _set_bubble(self, on: bool) -> None:
        self.shell.setProperty("bubble", "true" if on else "false")
        self.shell.style().unpolish(self.shell)
        self.shell.style().polish(self.shell)
