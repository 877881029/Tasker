from __future__ import annotations

from PySide6.QtCore import QEvent, QPoint, QRect, QSize, Qt
from PySide6.QtGui import (
    QColor,
    QGuiApplication,
    QIcon,
    QMouseEvent,
    QPainterPath,
    QPalette,
    QRegion,
)
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from tasker.resources import resource_path
from tasker.shell.detail import DetailWindow, detail_geometry
from tasker.shell.taskbar import apply_taskbar_icon
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
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)
        self.importance = QToolButton()
        self.importance.setObjectName("importance")
        self.importance.setFixedSize(20, 20)
        self.importance.setAutoRaise(True)
        self.importance.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.title = QLabel()
        self.title.setObjectName("titleField")
        self.title.setWordWrap(True)
        self.title.setMinimumHeight(72)
        self.title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.importance, 0, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.title, 1)
        self.apply_item(item)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._on_open(self.item_id)
            event.accept()
            return
        super().mousePressEvent(event)

    def apply_item(self, item: Item) -> None:
        self.setStyleSheet(
            f"QWidget#itemCard{{{card_style(item.state)}}}"
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
        self._brand = QLabel("事项")
        self._brand.setStyleSheet(f"color:{COBALT};font-weight:700;")
        self._brand.installEventFilter(self.chrome)
        self.search = QLineEdit()
        self.search.setObjectName("search")
        self.search.setPlaceholderText("查找…")
        self.search.textChanged.connect(self.refresh)
        self.add_btn = QToolButton()
        self.add_btn.setObjectName("addBtn")
        self.add_btn.setAutoRaise(True)
        self.add_btn.setText("+")
        self.add_btn.setFixedSize(32, 32)
        self.add_btn.setToolTip("新建事项")
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
        self.pin_btn.setCheckable(True)
        self.pin_btn.toggled.connect(self._toggle_pin)
        self.close_btn = QToolButton()
        self.close_btn.setObjectName("closeDock")
        self.close_btn.setAutoRaise(True)
        self.close_btn.setText("×")
        self.close_btn.setFixedSize(32, 32)
        self.close_btn.setToolTip("关闭")
        self.close_btn.clicked.connect(self._close_dock)
        header.addWidget(self._brand)
        header.addWidget(self.search, 1)
        header.addWidget(self.add_btn)
        header.addWidget(self.pin_btn)
        header.addWidget(self.close_btn)

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
        for widget in (self, scroll, scroll.viewport(), self.list_host):
            palette = widget.palette()
            palette.setColor(QPalette.ColorRole.Window, paper)
            palette.setColor(QPalette.ColorRole.Base, paper)
            widget.setPalette(palette)
            widget.setAutoFillBackground(True)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.shell = QWidget()
        self.shell.setObjectName("shell")
        self.shell.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        shell_layout = QVBoxLayout(self.shell)
        shell_layout.setContentsMargins(1, 1, 1, 1)
        shell_layout.setSpacing(0)
        shell_layout.addWidget(self.chrome)
        shell_layout.addWidget(scroll, 1)
        root.addWidget(self.shell)
        self._store.collapse_blank_drafts()
        self._place()
        self.refresh()
        self._icon_path = resource_path("assets", "icons", "tasker.ico")

    def _frame_flags(self, pinned: bool) -> Qt.WindowType:
        flags = Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint
        if pinned:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        return flags

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._apply_taskbar()
        self._apply_round_mask()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._apply_round_mask()

    def _apply_round_mask(self) -> None:
        path = QPainterPath()
        path.addRoundedRect(self.rect().adjusted(0, 0, -1, -1), 16, 16)
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))

    def _apply_taskbar(self) -> None:
        hwnd = int(self.winId())
        apply_taskbar_icon(hwnd, self._icon_path)

    def _place(self) -> None:
        screen = QGuiApplication.primaryScreen()
        avail = screen.availableGeometry() if screen else QRect(0, 0, 1920, 1080)
        self.setGeometry(geometry_for_screen(avail))

    def _toggle_pin(self, pinned: bool) -> None:
        self.setWindowFlags(self._frame_flags(pinned))
        self.show()
        self._apply_taskbar()

    def _close_dock(self) -> None:
        if self._detail is not None and self._detail.isVisible():
            self._detail.close_detail()
        self.close()

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
        for item in self._store.list_visible(query):
            self.list_layout.addWidget(ItemCard(self._store, item, self.open_detail))

    def open_detail(self, item_id: str) -> None:
        item = self._store.get(item_id)
        if item is None:
            return
        if self._detail is None:
            self._detail = DetailWindow(self._store, parent=self)
            self._detail.closed.connect(self.refresh)
        self._detail.load(item)
        screen = QGuiApplication.primaryScreen()
        avail = screen.availableGeometry() if screen else QRect(0, 0, 1920, 1080)
        self._detail.setGeometry(detail_geometry(avail, self.width()))
        if self.pin_btn.isChecked():
            self._detail.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self._detail.show()
        self._detail.raise_()
