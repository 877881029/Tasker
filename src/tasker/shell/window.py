from __future__ import annotations

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from tasker.resources import resource_path
from tasker.shell.detail import DetailWindow, detail_geometry
from tasker.store import Item, Store
from tasker.theme import (
    CHROME,
    COBALT,
    DONE_BG,
    INK,
    PAPER,
    PENDING_BG,
    URGENT_BG,
    card_style,
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
        layout.setContentsMargins(0, 0, 8, 0)
        self.color_bar = QToolButton()
        self.color_bar.setObjectName("colorBar")
        self.color_bar.setFixedWidth(10)
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
        layout.addWidget(self.done)
        self.apply_item(item)
        self.title.installEventFilter(self)

    def eventFilter(self, watched, event):
        from PySide6.QtCore import QEvent

        if watched is self.title and event.type() == QEvent.Type.FocusIn:
            self._on_open(self.item_id)
        return super().eventFilter(watched, event)

    def mousePressEvent(self, event) -> None:
        self._on_open(self.item_id)
        super().mousePressEvent(event)

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
        self._on_open(self.item_id)

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
        self.setStyleSheet(
            f"QWidget#dock{{background:{PAPER};color:{INK};}}"
            f"QLineEdit#search{{background:white;border:1px solid {CHROME};}}"
        )
        header = QHBoxLayout()
        label = QLabel("事项")
        label.setStyleSheet(f"color:{COBALT};font-weight:700;")
        self.search = QLineEdit()
        self.search.setObjectName("search")
        self.search.setPlaceholderText("查找…")
        self.search.textChanged.connect(self.refresh)
        self.add_btn = QPushButton("+")
        self.add_btn.clicked.connect(self._add)
        self.pin_btn = QToolButton()
        self.pin_btn.setText("钉")
        self.pin_btn.setCheckable(True)
        self.pin_btn.toggled.connect(self._toggle_pin)
        header.addWidget(label)
        header.addWidget(self.search, 1)
        header.addWidget(self.add_btn)
        header.addWidget(self.pin_btn)

        self.list_host = QWidget()
        self.list_layout = QVBoxLayout(self.list_host)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.list_host)
        scroll.setFrameShape(scroll.Shape.NoFrame)

        root = QVBoxLayout(self)
        root.addLayout(header)
        root.addWidget(scroll, 1)
        self._place()
        self.refresh()

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

    def _add(self) -> None:
        item = self._store.create()
        self.refresh()
        self._focus_card(item.id)
        self.open_detail(item.id)

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
            self._detail = DetailWindow(self._store)
        self._detail.load(item)
        screen = QGuiApplication.primaryScreen()
        avail = screen.availableGeometry() if screen else QRect(0, 0, 1920, 1080)
        self._detail.setGeometry(detail_geometry(avail, self.width()))
        if self.pin_btn.isChecked():
            self._detail.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self._detail.show()
        self._detail.raise_()
