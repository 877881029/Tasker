from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QRect, Qt, Signal
from PySide6.QtGui import QCloseEvent, QFont, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from tasker.journal import dump_journal, parse_journal, prepend_record
from tasker.resources import resource_path
from tasker.shell.journal_edit import JournalDocumentView, JournalEditor
from tasker.store import Item, Store
from tasker.theme import DONE_DOT, INK, PAPER, PENDING_DOT, URGENT_DOT


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
        self.editor = JournalEditor(self)
        self.editor.textChanged.connect(self.changed)
        self.document_view = JournalDocumentView(self)
        self.stack = QStackedWidget(self)
        self.stack.addWidget(self.document_view)
        self.stack.addWidget(self.editor)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self.stack)

    def load(self, body: str, when: datetime | None = None) -> None:
        self.editor.load_entries(parse_journal(body))
        self._show_document()

    def collect(self) -> str:
        return dump_journal(self._filled_entries())

    def latest_status(self) -> str:
        entries = self._filled_entries()
        if not entries:
            return ""
        return entries[0][1].strip().splitlines()[0] if entries[0][1].strip() else ""

    def head_edit(self) -> QPlainTextEdit:
        return self.editor

    def begin_write(self, when: datetime | None = None) -> None:
        moment = when or datetime.now()
        self.editor.load_entries(prepend_record(self.editor.entries(), moment))
        self.editor.setReadOnly(False)
        self.stack.setCurrentWidget(self.editor)
        self.editor.setFocus()
        cursor = self.editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        self.editor.setTextCursor(cursor)

    def set_all_readonly(self) -> None:
        self.editor.load_entries(self._filled_entries())
        self._show_document()

    def document_html(self) -> str:
        return self.document_view.document_html()

    def _show_document(self) -> None:
        self.editor.setReadOnly(True)
        self.document_view.set_entries(self._filled_entries())
        self.stack.setCurrentWidget(self.document_view)

    def _filled_entries(self) -> list[tuple[str, str]]:
        return [(stamp, text) for stamp, text in self.editor.entries() if text.strip()]


class DetailWindow(QWidget):
    closed = Signal()

    def __init__(self, store: Store, parent=None) -> None:
        super().__init__(parent)
        self._store = store
        self._item_id: str | None = None
        self.setStyleSheet(
            f"background:{PAPER};color:{INK};font-size:12pt;"
            "font-family:Candara,Calibri,\"Segoe UI\";"
        )
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
        bar.addWidget(self.delete_btn)

        self.journal = JournalPane()
        layout = QVBoxLayout(self)
        layout.addLayout(bar)
        layout.addWidget(self.journal, 1)

        self.title_edit.editingFinished.connect(self._save_title)
        QShortcut(QKeySequence("Ctrl+I"), self, activated=self.begin_write)
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.save_keep_open)
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

    def begin_write(self) -> None:
        self.journal.begin_write()

    def save_keep_open(self) -> None:
        self.save_all()
        self.journal.set_all_readonly()

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
