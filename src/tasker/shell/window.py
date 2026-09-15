from __future__ import annotations

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QColor, QGuiApplication, QIcon, QPalette
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
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
    DONE_BG,
    PAPER,
    PENDING_BG,
    URGENT_BG,
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
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        self.color_bar = QToolButton()
        self.color_bar.setObjectName("colorBar")
        self.color_bar.setFixedWidth(10)
        self.color_bar.setAutoRaise(True)
        self.color_bar.clicked.connect(self._cycle)
        self.title = QLineEdit()
        self.title.setText(item.title)
        self.title.setPlaceholderText("标题")
        self.title.editingFinished.connect(self._save_title)
        self.done = QCheckBox()
        self.done.setChecked(item.state == "done")
        self.done.toggled.connect(self._toggle_done)
        layout.addWidget(self.color_bar)
        layout.addWidget(self.title, 1)
        self.open_btn = QToolButton()
        self.open_btn.setObjectName("openDetail")
        self.open_btn.setAutoRaise(True)
        self.open_btn.setText("详情")
        self.open_btn.setToolTip("打开详情，写最新状态和正文")
        self.open_btn.clicked.connect(lambda: self._on_open(self.item_id))
        layout.addWidget(self.open_btn)
        layout.addWidget(self.done)
        self.apply_item(item)
    def mouseDoubleClickEvent(self, event) -> None:
        self._on_open(self.item_id)
        super().mouseDoubleClickEvent(event)

    def apply_item(self, item: Item) -> None:
        self.setStyleSheet(
            f"QWidget#itemCard{{{card_style(item.state)}}}"
            "QLineEdit{border:none;background:transparent;text-decoration:none;}"
        )
        self.done.blockSignals(True)
        self.done.setChecked(item.state == "done")
        self.done.blockSignals(False)
        bar = {"pending": PENDING_BG, "urgent": URGENT_BG, "done": DONE_BG}[item.state]
        self.color_bar.setStyleSheet(f"background:{bar};border:none;")

    def _cycle(self) -> None:
        item = self._store.cycle_color(self.item_id)
        self.apply_item(item)

    def _toggle_done(self, checked: bool) -> None:
        item = self._store.set_done(self.item_id, checked)
        self.apply_item(item)

    def _save_title(self) -> None:
        from dataclasses import replace

        item = self._store.get(self.item_id)
        if item is None:
            return
        self._store.save(replace(item, title=self.title.text()))


class DockWindow(QWidget):
    def __init__(self, store: Store, parent=None) -> None:
        super().__init__(parent)
        self._store = store
        self._detail: DetailWindow | None = None
        self.setWindowTitle("Tasker")
        self.setObjectName("dock")
        ico = resource_path("assets", "icons", "tasker.ico")
        if ico.exists():
            self.setWindowIcon(QIcon(str(ico)))
        self.setStyleSheet(dock_style())
        header = QHBoxLayout()
        header.setContentsMargins(12, 10, 12, 4)
        header.setSpacing(8)
        label = QLabel("事项")
        label.setStyleSheet(f"color:{COBALT};font-weight:700;")
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
        header.addWidget(label)
        header.addWidget(self.search, 1)
        header.addWidget(self.add_btn)
        header.addWidget(self.pin_btn)

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
        root.addLayout(header)
        root.addWidget(scroll, 1)
        self._store.collapse_blank_drafts()
        self._place()
        self.refresh()
        self._icon_path = resource_path("assets", "icons", "tasker.ico")

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._apply_taskbar()

    def _apply_taskbar(self) -> None:
        hwnd = int(self.winId())
        apply_taskbar_icon(hwnd, self._icon_path)

    def _place(self) -> None:
        screen = QGuiApplication.primaryScreen()
        avail = screen.availableGeometry() if screen else QRect(0, 0, 1920, 1080)
        self.setGeometry(geometry_for_screen(avail))

    def _toggle_pin(self, pinned: bool) -> None:
        flags = self.windowFlags()
        if pinned:
            self.setWindowFlags(flags | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(flags & ~Qt.WindowType.WindowStaysOnTopHint)
        self.show()
        self._apply_taskbar()

    def _add(self) -> None:
        item = self._store.ensure_draft()
        self.refresh()
        self._focus_card(item.id)

    def _focus_card(self, item_id: str) -> None:
        for i in range(self.list_layout.count()):
            widget = self.list_layout.itemAt(i).widget()
            if isinstance(widget, ItemCard) and widget.item_id == item_id:
                widget.title.setFocus()
                return

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
