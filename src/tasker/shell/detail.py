from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QRect, Signal
from PySide6.QtGui import QKeySequence, QShortcut, QIcon, QCloseEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QStackedWidget,
)

from tasker.preview.md_edit import MarkdownEdit
from tasker.preview.md_visual import MarkdownVisual
from tasker.resources import resource_path
from tasker.store import Item, Store
from tasker.theme import CHROME, COBALT, DONE_DOT, INK, PAPER, PENDING_DOT, URGENT_DOT


def detail_geometry(avail: QRect, dock_width: int) -> QRect:
    width = max(400, avail.width() - dock_width)
    return QRect(avail.x(), avail.y(), width, avail.height())


class DetailWindow(QWidget):
    closed = Signal()

    def __init__(self, store: Store, parent=None) -> None:
        super().__init__(parent)
        self._store = store
        self._item_id: str | None = None
        self.setWindowTitle("详情")
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setStyleSheet(f"background:{PAPER};color:{INK};")
        ico = resource_path("assets", "icons", "tasker.ico")
        if ico.exists():
            self.setWindowIcon(QIcon(str(ico)))

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("标题")
        self.save_btn = QPushButton("保存")
        self.save_btn.setObjectName("saveBtn")
        self.save_btn.setStyleSheet(
            f"background:{COBALT};color:white;border:none;padding:6px 14px;border-radius:4px;"
        )
        self.close_btn = QPushButton("关闭")
        self.close_btn.setObjectName("closeBtn")
        self.close_btn.setStyleSheet(
            f"background:{CHROME};color:{INK};border:1px solid {CHROME};padding:6px 14px;border-radius:4px;"
        )
        self.save_btn.clicked.connect(self.save_all)
        self.close_btn.clicked.connect(self.close_detail)

        self.done = QCheckBox("完成")
        self.done.setObjectName("doneBox")
        self.done.toggled.connect(self._toggle_done)
        self.importance = QToolButton()
        self.importance.setObjectName("importance")
        self.importance.setFixedSize(20, 20)
        self.importance.setAutoRaise(True)
        self.importance.setToolTip("切换普通 / 紧急")
        self.importance.clicked.connect(self._cycle)
        self.delete_btn = QPushButton("删除")
        self.delete_btn.setObjectName("deleteBtn")
        self.delete_btn.setStyleSheet(
            f"background:transparent;color:#b91c1c;border:none;padding:6px 10px;"
        )
        self.delete_btn.clicked.connect(self.delete_item)

        bar = QHBoxLayout()
        bar.addWidget(self.importance)
        bar.addWidget(self.title_edit, 1)
        bar.addWidget(self.done)
        bar.addWidget(self.save_btn)
        bar.addWidget(self.close_btn)
        bar.addWidget(self.delete_btn)

        self.status_pin = QPlainTextEdit()
        self.status_pin.setPlaceholderText("最新状态（置顶）")
        self.status_pin.setFixedHeight(72)
        pin_label = QLabel("最新状态")
        self.stack = QStackedWidget()
        self.visual = MarkdownVisual()
        self.editor = MarkdownEdit(store, "")
        self.stack.addWidget(self.visual)
        self.stack.addWidget(self.editor)

        layout = QVBoxLayout(self)
        layout.addLayout(bar)
        layout.addWidget(pin_label)
        layout.addWidget(self.status_pin)
        hint = QLabel("Ctrl+I 编辑正文 · Ctrl+T 预览 · Esc 关闭")
        hint.setStyleSheet(f"color:{INK};font-size:11px;")
        layout.addWidget(hint)
        layout.addWidget(self.stack, 1)

        self.title_edit.editingFinished.connect(self._save_title)
        self.status_pin.textChanged.connect(self._save_pin)
        QShortcut(QKeySequence("Ctrl+I"), self, activated=self.show_edit)
        QShortcut(QKeySequence("Ctrl+T"), self, activated=self.show_visual)
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.save_all)
        QShortcut(QKeySequence("Esc"), self, activated=self.close_detail)

    def load(self, item: Item) -> None:
        self._item_id = item.id
        self.editor.set_item_id(item.id)
        self.title_edit.blockSignals(True)
        self.status_pin.blockSignals(True)
        self.done.blockSignals(True)
        self.title_edit.setText(item.title)
        self.status_pin.setPlainText(item.status_pin)
        self.editor.setPlainText(item.body_md)
        self.done.setChecked(item.state == "done")
        self._paint_importance(item)
        self.title_edit.blockSignals(False)
        self.status_pin.blockSignals(False)
        self.done.blockSignals(False)
        self.show_visual()

    def save_all(self) -> None:
        self._save_title()
        self._save_pin()
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
            f"QToolButton{{background:{dot};border:none;border-radius:10px;}}"
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._item_id:
            self.save_all()
        event.accept()
        self.closed.emit()

    def show_edit(self) -> None:
        self.stack.setCurrentWidget(self.editor)

    def show_visual(self) -> None:
        self._save_body()
        item = self._store.get(self._item_id) if self._item_id else None
        if item:
            base = str(Path(self._store._db_file).parent)
            self.visual.set_markdown(item.body_md, base)
        self.stack.setCurrentWidget(self.visual)

    def _save_title(self) -> None:
        if not self._item_id:
            return
        item = self._store.get(self._item_id)
        if item is None:
            return
        from dataclasses import replace

        self._store.save(replace(item, title=self.title_edit.text()))

    def _save_pin(self) -> None:
        if not self._item_id:
            return
        item = self._store.get(self._item_id)
        if item is None:
            return
        from dataclasses import replace

        self._store.save(replace(item, status_pin=self.status_pin.toPlainText()))

    def _save_body(self) -> None:
        if not self._item_id:
            return
        item = self._store.get(self._item_id)
        if item is None:
            return
        from dataclasses import replace

        self._store.save(replace(item, body_md=self.editor.toPlainText()))
