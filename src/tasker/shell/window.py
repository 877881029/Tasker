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
    QPainterPath,
    QPalette,
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
from tasker.store import Item, Store
from tasker.theme import (
    COBALT,
    DONE_DOT,
    INK,
    MUTED,
    PAPER,
    PENDING_DOT,
    URGENT_DOT,
    card_style,
    dock_style,
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
    return 16


def round_window_mask(rect: QRect, radius: int) -> QRegion | None:
    if radius <= 0:
        return None
    path = QPainterPath()
    path.addRoundedRect(QRectF(rect), float(radius), float(radius))
    return QRegion(path.toFillPolygon().toPolygon())


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
    def __init__(self, store: Store, item: Item, on_open, parent=None) -> None:
        super().__init__(parent)
        self._store = store
        self.item_id = item.id
        self._on_open = on_open
        self.setObjectName("itemCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self.setMinimumHeight(88)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)
        self.importance = QToolButton()
        self.importance.setObjectName("importance")
        self.importance.setFixedSize(20, 20)
        self.importance.setAutoRaise(True)
        self.importance.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.importance.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.title = QLabel()
        self.title.setObjectName("titleField")
        self.title.setWordWrap(True)
        self.title.setMinimumHeight(72)
        self.title.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.importance, 0, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.title, 1)
        self._selected = False
        self.apply_item(item)

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        item = self._store.get(self.item_id)
        if item is not None:
            self.apply_item(item)

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
        super().keyPressEvent(event)

    def apply_item(self, item: Item) -> None:
        edge = f"border:2px solid {COBALT};" if self._selected else ""
        self.setStyleSheet(
            f"QWidget#itemCard{{{card_style(item.state)}{edge}}}"
            f"QWidget#itemCard:hover{{border:1px solid {COBALT};}}"
        )
        dot = {"pending": PENDING_DOT, "urgent": URGENT_DOT, "done": DONE_DOT}[item.state]
        self.importance.setStyleSheet(
            f"QToolButton{{background:{dot};border:none;border-radius:10px;}}"
        )
        text = item.title.strip()
        self.title.setText(text or "标题")
        color = INK if text else MUTED
        self.title.setStyleSheet(f"color:{color};font-size:15px;")
        state = {"pending": "普通", "urgent": "紧急", "done": "已完成"}[item.state]
        name = text or "无标题"
        self.setAccessibleName(f"{state}任务：{name}")
        self.setAccessibleDescription("按 Enter 或空格打开详情")
        self.setToolTip(f"{state} · {name}")
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
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        ico = resource_path("assets", "icons", "tasker.ico")
        if ico.exists():
            self.setWindowIcon(QIcon(str(ico)))
        self.setStyleSheet(dock_style())
        self.chrome = ChromeBar(self)
        header = QHBoxLayout(self.chrome)
        header.setContentsMargins(12, 10, 12, 4)
        header.setSpacing(8)
        self.search = QLineEdit()
        self.search.setObjectName("search")
        self.search.setPlaceholderText("查找…")
        self.search.setAccessibleName("搜索事项")
        self.search.textChanged.connect(self.refresh)
        self.add_btn = QToolButton()
        self.add_btn.setObjectName("addBtn")
        self.add_btn.setAutoRaise(True)
        self.add_btn.setText("+")
        self.add_btn.setFixedSize(32, 32)
        self.add_btn.setToolTip("新建事项")
        self.add_btn.setAccessibleName("新建事项")
        self.add_btn.clicked.connect(self._add)
        self.pin_btn = QToolButton()
        self.pin_btn.setObjectName("pinBtn")
        self.pin_btn.setAutoRaise(True)
        self.pin_btn.setText("")
        pin_icon = resource_path("assets", "icons", "pin.svg")
        if pin_icon.exists():
            self.pin_btn.setIcon(QIcon(str(pin_icon)))
            self.pin_btn.setIconSize(QSize(18, 18))
        self.pin_btn.setFixedSize(32, 32)
        self.pin_btn.setToolTip("钉在其它窗口上面")
        self.pin_btn.setAccessibleName("置顶窗口")
        self.pin_btn.setCheckable(True)
        self.pin_btn.toggled.connect(self._toggle_pin)
        self.close_btn = QToolButton()
        self.close_btn.setObjectName("closeDock")
        self.close_btn.setAutoRaise(True)
        self.close_btn.setText("×")
        self.close_btn.setFixedSize(32, 32)
        self.close_btn.setToolTip("关闭")
        self.close_btn.setAccessibleName("隐藏到托盘")
        self.close_btn.clicked.connect(self._close_dock)
        header.addWidget(self.search, 1)
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
        self.list_layout.setContentsMargins(12, 8, 12, 12)
        self.list_layout.setSpacing(10)
        scroll = QScrollArea()
        scroll.setObjectName("listScroll")
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.list_host)
        scroll.setFrameShape(scroll.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        paper = QColor(PAPER)
        for widget in (scroll, scroll.viewport(), self.list_host):
            palette = widget.palette()
            palette.setColor(QPalette.ColorRole.Window, paper)
            palette.setColor(QPalette.ColorRole.Base, paper)
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
        self._detail_box.setContentsMargins(12, 12, 4, 12)
        self._detail_box.setSpacing(0)
        self.detail_host.hide()
        self.detail_host.setMaximumWidth(0)

        self.notch = QWidget()
        self.notch.setObjectName("notch")
        self.notch.setFixedWidth(16)
        self.notch.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.notch.setStyleSheet(f"background:{PAPER};")
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
        menu = QMenu()
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
        query = self.search.text()
        while self.list_layout.count():
            child = self.list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        previous: QWidget = self.close_btn
        for item in self._store.list_visible(query):
            card = ItemCard(self._store, item, self.open_detail)
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
        self._detail.load(item)
        self.detail_host.setMaximumWidth(16777215)
        self.notch.show()
        self.detail_host.show()
        self._set_bubble(True)
        self._place()
        self.refresh()
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
