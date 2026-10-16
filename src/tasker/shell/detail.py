from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import (
    QCloseEvent,
    QColor,
    QIcon,
    QKeySequence,
    QPainter,
    QPixmap,
    QShortcut,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from tasker.i18n import tr
from tasker.deadline import build_deadline_menu, deadline_label
from tasker.journal import dump_journal, parse_journal, prepend_record
from tasker.resources import resource_path
from tasker.shell.journal_edit import JournalDocumentView, JournalEditor
from tasker.shell.status import apply_status, build_status_menu
from tasker.store import Item, Store
from tasker.theme import (
    CARD,
    COBALT,
    HOVER,
    INK,
    LINE,
    LINE_STRONG,
    MUTED,
    PAPER,
    SELECTED,
    STATE_DOT,
    STATE_LABEL,
    STATE_PILL,
    ui_font,
)


def coalesce_journal_pull(
    current: list[tuple[str, str]], pulled: list[tuple[str, str]]
) -> list[tuple[str, str]]:
    if not pulled:
        return current
    if not any((text or "").strip() for _stamp, text in pulled):
        return current
    merged: list[tuple[str, str]] = []
    for index, (stamp, text) in enumerate(pulled):
        if (text or "").strip():
            merged.append((stamp, text))
            continue
        if index < len(current) and (current[index][1] or "").strip():
            old_stamp, old_text = current[index]
            merged.append((old_stamp or stamp, old_text))
        else:
            merged.append((stamp, text))
    if len(current) > len(pulled):
        merged.extend(current[len(pulled) :])
    return merged


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
        self._writing = False
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
        cursor = self.editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        self.editor.setTextCursor(cursor)
        self._writing = True
        self.stack.setCurrentWidget(self.editor)
        self.editor.setFocus()

    def commit_view(self) -> None:
        return

    def set_all_readonly(self) -> None:
        self.commit_view()
        self._writing = False
        self.editor.load_entries(self._filled_entries())
        self.editor.setReadOnly(True)
        self._show_document()

    def document_html(self) -> str:
        return self.document_view.document_html()

    def _show_document(self) -> None:
        self.editor.setReadOnly(True)
        self.document_view.set_entries(self._filled_entries())
        self.stack.setCurrentWidget(self.document_view)

    def _filled_entries(self) -> list[tuple[str, str]]:
        return [(stamp, text) for stamp, text in self.editor.entries() if text.strip()]


def _dot_icon(color: str, size: int = 8) -> QIcon:
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(color))
    painter.drawEllipse(0, 0, size, size)
    painter.end()
    return QIcon(pixmap)


class DetailWindow(QWidget):
    closed = Signal()
    changed = Signal(str)
    deleted = Signal(str, str, str)
    _READ_STATUS = "{write} 写入 · {save} 保存 · Esc 收起"
    _WRITE_STATUS = "正在写入 · {save} 保存 · Esc 保存并收起"
    _SAVED_STATUS = "已保存 {time} · {write} 继续写入 · Esc 收起"

    def __init__(self, store: Store, parent=None) -> None:
        super().__init__(parent)
        self._store = store
        self._item_id: str | None = None
        self._state = "pending"
        self.setObjectName("detail")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            f"QWidget#detail{{background:{PAPER};color:{INK};}}"
        )
        self.setFont(ui_font(13))
        if parent is None:
            self.setWindowTitle(tr("详情"))
            self.setWindowFlags(
                Qt.WindowType.Tool
                | Qt.WindowType.WindowTitleHint
                | Qt.WindowType.WindowCloseButtonHint
            )
        ico = resource_path("assets", "icons", "tasker.ico")
        if ico.exists():
            self.setWindowIcon(QIcon(str(ico)))

        self.status_btn = QToolButton()
        self.status_btn.setObjectName("statusPill")
        self.status_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.status_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.status_btn.setIconSize(QSize(8, 8))
        self.status_btn.setFixedHeight(26)
        self.status_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.status_btn.setToolTip(tr("改状态：普通 / 紧急 / 已完成"))
        self.status_btn.setAccessibleDescription(tr("打开菜单选择普通、紧急或已完成"))

        self._deadline: datetime | None = None
        self.deadline_btn = QToolButton()
        self.deadline_btn.setObjectName("deadlinePill")
        self.deadline_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.deadline_btn.setFixedHeight(26)
        self.deadline_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.deadline_btn.setToolTip(tr("设置截止时间（仅紧急任务）"))
        self.deadline_btn.setAccessibleDescription(tr("打开菜单选择或清除截止时间"))
        self.deadline_btn.setStyleSheet(
            f"QToolButton#deadlinePill{{background:{CARD};color:{INK};"
            f"border:1px solid {LINE_STRONG};border-radius:8px;padding:0 10px;"
            "font-size:12px;font-weight:600;}"
            f"QToolButton#deadlinePill:hover{{background:{HOVER};}}"
            f"QToolButton#deadlinePill:focus{{border:2px solid {COBALT};}}"
            "QToolButton#deadlinePill::menu-indicator{image:none;width:0;}"
        )
        self.deadline_btn.hide()

        self.title_edit = QLineEdit()
        self.title_edit.setObjectName("detailTitle")
        self.title_edit.setPlaceholderText(tr("标题"))
        self.title_edit.setAccessibleName(tr("任务标题"))
        self.title_edit.setFrame(False)
        self.title_edit.setMinimumHeight(38)
        self.title_edit.setStyleSheet(
            f"QLineEdit#detailTitle{{background:transparent;color:{INK};"
            "border:2px solid transparent;border-radius:6px;padding:2px 6px;"
            f"selection-background-color:{COBALT};}}"
            f"QLineEdit#detailTitle:hover{{background:{HOVER};}}"
            f"QLineEdit#detailTitle:focus{{background:{CARD};border:2px solid {COBALT};}}"
        )
        self.title_edit.setFont(ui_font(20, 600))

        self.delete_btn = QToolButton()
        self.delete_btn.setObjectName("deleteBtn")
        trash = resource_path("assets", "icons", "trash.svg")
        if trash.exists():
            self.delete_btn.setIcon(QIcon(str(trash)))
        self.delete_btn.setIconSize(QSize(16, 16))
        self.delete_btn.setFixedHeight(32)
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._paint_delete_btn()
        self.delete_btn.clicked.connect(self.delete_item)

        bar = QHBoxLayout()
        bar.setContentsMargins(0, 0, 0, 0)
        bar.setSpacing(8)
        bar.addWidget(self.status_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        bar.addWidget(self.deadline_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        bar.addWidget(self.title_edit, 1)
        bar.addWidget(self.delete_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        self.journal = JournalPane()

        self.footer = QFrame()
        self.footer.setObjectName("detailFooter")
        self.footer.setStyleSheet(
            f"QFrame#detailFooter{{background:transparent;border:none;"
            f"border-top:1px solid {LINE};}}"
        )
        footer_row = QHBoxLayout(self.footer)
        footer_row.setContentsMargins(4, 8, 4, 0)
        footer_row.setSpacing(6)
        self.journal_dot = QLabel("●")
        self.journal_dot.setObjectName("journalDot")
        self.journal_dot.setStyleSheet(f"color:{COBALT};font-size:10px;")
        self.journal_dot.hide()
        self._keys = {"write": "Ctrl+I", "save": "Ctrl+S"}
        self.journal_status = QLabel(self._status_text(self._READ_STATUS))
        self.journal_status.setObjectName("journalStatus")
        self.journal_status.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.journal_status.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.journal_status.setAccessibleName(tr("日志操作状态"))
        self.journal_status.setStyleSheet(f"color:{MUTED};font-size:12px;")
        footer_row.addWidget(self.journal_dot)
        footer_row.addWidget(self.journal_status, 1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 14, 16, 10)
        layout.setSpacing(10)
        layout.addLayout(bar)
        layout.addWidget(self.journal, 1)
        layout.addWidget(self.footer)

        self.title_edit.editingFinished.connect(self._save_title)
        self._write_shortcut = QShortcut(QKeySequence("Ctrl+I"), self, activated=self.begin_write)
        self._save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self, activated=self.save_keep_open)
        QShortcut(QKeySequence("Esc"), self, activated=self.close_detail)

    def load(self, item: Item) -> None:
        self._item_id = item.id
        self.title_edit.blockSignals(True)
        self.title_edit.setText(item.title)
        self.title_edit.setCursorPosition(0)
        self.title_edit.blockSignals(False)
        self.sync_status(item)
        self.journal.load(item.body_md)
        self._set_journal_status(self._status_text(self._READ_STATUS))

    def sync_status(self, item: Item) -> None:
        if item.id != self._item_id:
            return
        self._state = item.state
        self._deadline = item.deadline
        self._paint_status()
        self._paint_deadline()

    def set_deadline(self, when: datetime | None) -> None:
        if not self._item_id:
            return
        item = self._store.set_deadline(self._item_id, when)
        self._deadline = item.deadline
        self._paint_deadline()
        self.changed.emit(item.id)

    def set_status(self, state: str) -> None:
        if not self._item_id:
            return
        item = apply_status(self._store, self._item_id, state)
        self.sync_status(item)
        self.changed.emit(item.id)

    def begin_write(self) -> None:
        self.journal.begin_write()
        self._set_journal_status(self._status_text(self._WRITE_STATUS), writing=True)

    def save_keep_open(self) -> None:
        self.save_all()
        self.journal.set_all_readonly()
        stamp = datetime.now().strftime("%H:%M")
        self._set_journal_status(self._status_text(self._SAVED_STATUS, time=stamp))

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
        item_id = self._item_id
        self.save_all()
        raw = self._store.read_raw(item_id) or ""
        title = self.title_edit.text().strip()
        self._store.delete(item_id)
        self._item_id = None
        self.hide()
        self.deleted.emit(item_id, raw, title)
        self.closed.emit()

    def _paint_delete_btn(self) -> None:
        self.delete_btn.setText(tr("删除"))
        self.delete_btn.setAccessibleName(tr("删除任务"))
        self.delete_btn.setToolTip(tr("删除"))
        self.delete_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.delete_btn.setFixedWidth(32)
        self.delete_btn.setStyleSheet(
            "QToolButton#deleteBtn{background:transparent;border:none;"
            "border-radius:6px;padding:0;}"
            f"QToolButton#deleteBtn:hover{{background:{HOVER};}}"
            f"QToolButton#deleteBtn:pressed{{background:{SELECTED};}}"
            f"QToolButton#deleteBtn:focus{{border:2px solid {COBALT};}}"
        )

    def _status_text(self, template: str, **extra) -> str:
        return tr(template, **self._keys, **extra)

    def set_shortcut_keys(self, write: str, save: str) -> None:
        self._keys = {"write": write, "save": save}
        self._write_shortcut.setKey(QKeySequence(write))
        self._save_shortcut.setKey(QKeySequence(save))
        if self.journal_dot.isHidden():
            self._set_journal_status(self._status_text(self._READ_STATUS))

    def _set_journal_status(self, text: str, *, writing: bool = False) -> None:
        self.journal_status.setText(text)
        self.journal_dot.setVisible(writing)

    def _paint_status(self) -> None:
        state = self._state
        bg, line = STATE_PILL[state]
        dot = STATE_DOT[state]
        label = tr(STATE_LABEL[state])
        self.status_btn.setText(f"{label}  ▾")
        self.status_btn.setIcon(_dot_icon(dot))
        self.status_btn.setAccessibleName(tr("任务状态：{label}", label=label))
        self.status_btn.setStyleSheet(
            f"QToolButton#statusPill{{background:{bg};color:{INK};"
            f"border:1px solid {line};border-radius:13px;padding:0 10px 0 8px;"
            "font-size:12px;font-weight:600;}"
            f"QToolButton#statusPill:hover{{border:1px solid {dot};}}"
            f"QToolButton#statusPill:focus{{border:2px solid {COBALT};}}"
            "QToolButton#statusPill::menu-indicator{image:none;width:0;}"
        )
        old = self.status_btn.menu()
        self.status_btn.setMenu(build_status_menu(state, self.set_status, self))
        if old is not None:
            old.deleteLater()

    def _paint_deadline(self) -> None:
        if self._state != "urgent":
            self.deadline_btn.hide()
            return
        if self._deadline is None:
            text = tr("设置 DDL  ▾")
            self.deadline_btn.setAccessibleName(tr("截止时间：未设置"))
        else:
            label = deadline_label(self._deadline)
            text = f"DDL {label}  ▾"
            self.deadline_btn.setAccessibleName(tr("截止时间：{label}", label=label))
        self.deadline_btn.setText(text)
        old = self.deadline_btn.menu()
        self.deadline_btn.setMenu(
            build_deadline_menu(self._deadline, self.set_deadline, self)
        )
        if old is not None:
            old.deleteLater()
        self.deadline_btn.show()

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
        if item.title == self.title_edit.text():
            return
        from dataclasses import replace

        self._store.save(replace(item, title=self.title_edit.text()))
        self.changed.emit(item.id)

    def _save_body(self) -> None:
        if not self._item_id:
            return
        item = self._store.get(self._item_id)
        if item is None:
            return
        from dataclasses import replace

        self.journal.commit_view()
        body = self.journal.collect()
        pin = self.journal.latest_status()
        self._store.save(replace(item, body_md=body, status_pin=pin))
