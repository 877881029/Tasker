from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QEvent, QRect, Qt, Signal
from PySide6.QtGui import QCloseEvent, QFont, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from tasker.journal import dump_journal, ensure_current, parse_journal, stamp_for
from tasker.resources import resource_path
from tasker.store import Item, Store
from tasker.theme import CHROME, COBALT, DONE_DOT, INK, MUTED, PAPER, PENDING_DOT, URGENT_DOT


def detail_geometry(avail: QRect, dock_width: int) -> QRect:
    width = max(400, avail.width() - dock_width)
    return QRect(avail.x(), avail.y(), width, avail.height())


def expanded_geometry(avail: QRect) -> QRect:
    return QRect(avail.x(), avail.y(), avail.width(), avail.height())


class JournalPane(QWidget):
    changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("journal")
        self._rows: list[tuple[QLabel, QPlainTextEdit]] = []
        self._host = QWidget()
        self._list = QVBoxLayout(self._host)
        self._list.setContentsMargins(0, 0, 8, 8)
        self._list.setSpacing(10)
        self._list.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self._host)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll.setStyleSheet(f"background:{PAPER};border:none;")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self.scroll)

    def load(self, body: str, when: datetime | None = None) -> None:
        moment = when or datetime.now()
        self._rebuild(ensure_current(parse_journal(body), moment))

    def collect(self) -> str:
        return dump_journal(self._from_ui())

    def latest_status(self) -> str:
        entries = self._from_ui()
        if not entries:
            return ""
        return entries[0][1].strip().splitlines()[0] if entries[0][1].strip() else ""

    def head_edit(self) -> QPlainTextEdit:
        return self._rows[0][1]

    def capture_input(self, when: datetime | None = None) -> None:
        moment = when or datetime.now()
        self._rebuild(ensure_current(self._from_ui(), moment))
        self._focus_head()

    def eventFilter(self, watched, event) -> bool:
        if event.type() == QEvent.Type.KeyPress and isinstance(watched, QPlainTextEdit):
            text = event.text()
            if text and text.isprintable():
                stamp = stamp_for(datetime.now())
                head = self.head_edit()
                if self._rows[0][0].text() != stamp or watched is not head:
                    self.capture_input()
                    head = self.head_edit()
                    head.insertPlainText(text)
                    return True
        return super().eventFilter(watched, event)

    def _from_ui(self) -> list[tuple[str, str]]:
        return [(label.text(), edit.toPlainText()) for label, edit in self._rows]

    def _rebuild(self, entries: list[tuple[str, str]]) -> None:
        while self._list.count():
            child = self._list.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self._rows = []
        for stamp, text in entries:
            row = QWidget()
            row.setStyleSheet(f"background:{PAPER};")
            line = QHBoxLayout(row)
            line.setContentsMargins(0, 0, 0, 0)
            line.setSpacing(12)
            gutter = QLabel(stamp)
            gutter.setFixedWidth(118)
            gutter.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
            color = COBALT if not self._rows else MUTED
            gutter.setStyleSheet(
                f"color:{color};font-family:Consolas,'Cascadia Mono',monospace;"
                "font-size:13px;font-weight:600;padding-top:4px;"
            )
            editor = QPlainTextEdit()
            editor.setPlainText(text)
            editor.setFrameShape(QPlainTextEdit.Shape.NoFrame)
            editor.setStyleSheet(
                f"QPlainTextEdit{{background:{PAPER};color:{INK};border:none;font-size:15px;}}"
            )
            editor.setPlaceholderText("记录…")
            editor.installEventFilter(self)
            editor.textChanged.connect(self.changed)
            line.addWidget(gutter, 0)
            line.addWidget(editor, 1)
            self._list.addWidget(row)
            self._rows.append((gutter, editor))
        self._focus_head()

    def _focus_head(self) -> None:
        if not self._rows:
            return
        edit = self._rows[0][1]
        edit.setFocus()
        cursor = edit.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        edit.setTextCursor(cursor)
        self.scroll.verticalScrollBar().setValue(0)


class DetailWindow(QWidget):
    closed = Signal()

    def __init__(self, store: Store, parent=None) -> None:
        super().__init__(parent)
        self._store = store
        self._item_id: str | None = None
        self.setStyleSheet(f"background:{PAPER};color:{INK};font-size:16px;")
        if parent is None:
            self.setWindowTitle("详情")
            self.setWindowFlags(
                Qt.WindowType.Tool
                | Qt.WindowType.WindowTitleHint
                | Qt.WindowType.WindowCloseButtonHint
            )
        ico = resource_path("assets", "icons", "tasker.ico")
        if ico.exists():
            self.setWindowIcon(QIcon(str(ico)))

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("标题")
        self.title_edit.setMinimumHeight(40)
        title_font = QFont(self.title_edit.font())
        title_font.setPointSize(16)
        self.title_edit.setFont(title_font)
        self.save_btn = QPushButton("保存")
        self.save_btn.setObjectName("saveBtn")
        self.save_btn.setStyleSheet(
            f"background:{COBALT};color:white;border:none;padding:10px 18px;"
            "border-radius:6px;font-size:15px;"
        )
        self.close_btn = QPushButton("关闭")
        self.close_btn.setObjectName("closeBtn")
        self.close_btn.setStyleSheet(
            f"background:{CHROME};color:{INK};border:1px solid {CHROME};"
            "padding:10px 18px;border-radius:6px;font-size:15px;"
        )
        self.save_btn.clicked.connect(self.save_all)
        self.close_btn.clicked.connect(self.close_detail)

        self.done = QCheckBox("完成")
        self.done.setObjectName("doneBox")
        self.done.setStyleSheet("font-size:15px;")
        self.done.toggled.connect(self._toggle_done)
        self.importance = QToolButton()
        self.importance.setObjectName("importance")
        self.importance.setFixedSize(32, 32)
        self.importance.setAutoRaise(True)
        self.importance.setToolTip("切换普通 / 紧急")
        self.importance.clicked.connect(self._cycle)
        self.delete_btn = QPushButton("删除")
        self.delete_btn.setObjectName("deleteBtn")
        self.delete_btn.setStyleSheet(
            "background:transparent;color:#b91c1c;border:none;padding:10px 14px;font-size:15px;"
        )
        self.delete_btn.clicked.connect(self.delete_item)

        bar = QHBoxLayout()
        bar.setSpacing(10)
        bar.addWidget(self.importance)
        bar.addWidget(self.title_edit, 1)
        bar.addWidget(self.done)
        bar.addWidget(self.save_btn)
        bar.addWidget(self.close_btn)
        bar.addWidget(self.delete_btn)

        self.journal = JournalPane()
        self.journal.changed.connect(self._save_body)
        layout = QVBoxLayout(self)
        layout.addLayout(bar)
        layout.addWidget(self.journal, 1)

        self.title_edit.editingFinished.connect(self._save_title)
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.save_all)
        QShortcut(QKeySequence("Esc"), self, activated=self.close_detail)

    def load(self, item: Item) -> None:
        self._item_id = item.id
        self.title_edit.blockSignals(True)
        self.done.blockSignals(True)
        self.title_edit.setText(item.title)
        self.done.setChecked(item.state == "done")
        self._paint_importance(item)
        self.title_edit.blockSignals(False)
        self.done.blockSignals(False)
        self.journal.load(item.body_md)

    def save_all(self) -> None:
        self._save_title()
        self._save_body()

    def close_detail(self) -> None:
        self.save_all()
        self.hide()
        self.closed.emit()

    def delete_item(self) -> None:
        if not self._item_id:
            return
        self._store.delete(self._item_id)
        self._item_id = None
        self.hide()
        self.closed.emit()

    def _toggle_done(self, checked: bool) -> None:
        if not self._item_id:
            return
        item = self._store.set_done(self._item_id, checked)
        self._paint_importance(item)

    def _cycle(self) -> None:
        if not self._item_id:
            return
        item = self._store.cycle_color(self._item_id)
        self._paint_importance(item)
        self.done.blockSignals(True)
        self.done.setChecked(item.state == "done")
        self.done.blockSignals(False)

    def _paint_importance(self, item: Item) -> None:
        dot = {"pending": PENDING_DOT, "urgent": URGENT_DOT, "done": DONE_DOT}[item.state]
        self.importance.setStyleSheet(
            f"QToolButton{{background:{dot};border:none;border-radius:16px;}}"
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._item_id:
            self.save_all()
        event.accept()
        self.closed.emit()

    def _save_title(self) -> None:
        if not self._item_id:
            return
        item = self._store.get(self._item_id)
        if item is None:
            return
        from dataclasses import replace

        self._store.save(replace(item, title=self.title_edit.text()))

    def _save_body(self) -> None:
        if not self._item_id:
            return
        item = self._store.get(self._item_id)
        if item is None:
            return
        from dataclasses import replace

        body = self.journal.collect()
        pin = self.journal.latest_status()
        self._store.save(replace(item, body_md=body, status_pin=pin))
