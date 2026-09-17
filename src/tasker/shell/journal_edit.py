from __future__ import annotations

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QResizeEvent,
    QTextBlock,
    QTextBlockUserData,
    QTextCursor,
)
from PySide6.QtWidgets import QFrame, QPlainTextEdit, QSizePolicy, QWidget

from tasker.theme import COBALT, INK, MUTED, PAPER


class StampData(QTextBlockUserData):
    def __init__(self, stamp: str) -> None:
        super().__init__()
        self.stamp = stamp


class _StampGutter(QWidget):
    def __init__(self, editor: JournalEditor) -> None:
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(JournalEditor.GUTTER_WIDTH, 0)

    def paintEvent(self, event) -> None:  # noqa: N802
        self._editor.paint_stamps(event)


class JournalEditor(QPlainTextEdit):
    GUTTER_WIDTH = 118

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("journalEditor")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setPlaceholderText("记录…")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFont(_document_font(16))
        self._gutter_font = QFont(self.font())
        self._gutter_font.setPixelSize(13)
        self._gutter_font.setWeight(self.font().weight())
        self.setStyleSheet(
            f"QPlainTextEdit#journalEditor{{background:{PAPER};color:{INK};border:none;}}"
        )
        self._gutter = _StampGutter(self)
        self.blockCountChanged.connect(lambda _n: self._sync_gutter())
        self.updateRequest.connect(self._on_update_request)
        self._sync_gutter()

    def gutter(self) -> QWidget:
        return self._gutter

    def gutter_font(self) -> QFont:
        return QFont(self._gutter_font)

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._sync_gutter()

    def load_entries(self, entries: list[tuple[str, str]]) -> None:
        self.clear()
        if not entries:
            self._sync_gutter()
            return
        cursor = QTextCursor(self.document())
        cursor.beginEditBlock()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        for index, (stamp, text) in enumerate(entries):
            if index:
                cursor.insertBlock()
                cursor.insertBlock()
            start = cursor.block()
            lines = (text or "").split("\n")
            cursor.insertText(lines[0])
            for line in lines[1:]:
                cursor.insertBlock()
                cursor.insertText(line)
            self._mark_record(start, stamp)
        cursor.endEditBlock()
        self._sync_gutter()

    def entries(self) -> list[tuple[str, str]]:
        found: list[tuple[str, str]] = []
        stamp: str | None = None
        parts: list[str] = []
        block = self.document().begin()
        while block.isValid():
            marked = _stamp_of(block)
            if marked:
                if stamp is not None:
                    found.append((stamp, "\n".join(parts).strip("\n")))
                stamp = marked
                parts = [block.text()]
            elif stamp is None:
                stamp = ""
                parts = [block.text()]
            else:
                parts.append(block.text())
            block = block.next()
        if stamp is not None:
            found.append((stamp, "\n".join(parts).strip("\n")))
        return found

    def paint_stamps(self, event) -> None:
        painter = QPainter(self._gutter)
        painter.fillRect(event.rect(), QColor(PAPER))
        painter.setFont(self._gutter_font)
        newest = self._newest_stamp_block()
        block = self.firstVisibleBlock()
        while block.isValid():
            geo = self.blockBoundingGeometry(block).translated(self.contentOffset())
            top = round(geo.top())
            if top > event.rect().bottom():
                break
            stamp = _stamp_of(block)
            if stamp and geo.bottom() >= event.rect().top():
                color = COBALT if newest is not None and block.blockNumber() == newest.blockNumber() else MUTED
                painter.setPen(QColor(color))
                painter.drawText(
                    0,
                    top,
                    self.GUTTER_WIDTH - 8,
                    max(round(self.blockBoundingRect(block).height()), self.fontMetrics().lineSpacing()),
                    int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop),
                    stamp,
                )
            block = block.next()
        painter.end()

    def _mark_record(self, block: QTextBlock, stamp: str) -> None:
        cursor = QTextCursor(block)
        cursor.block().setUserData(StampData(stamp) if stamp else None)

    def _newest_stamp_block(self) -> QTextBlock | None:
        block = self.document().begin()
        while block.isValid():
            if _stamp_of(block):
                return block
            block = block.next()
        return None

    def _on_update_request(self, rect: QRect, dy: int) -> None:
        if dy:
            self._gutter.scroll(0, dy)
        else:
            self._gutter.update(0, rect.y(), self._gutter.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._sync_gutter()

    def _sync_gutter(self) -> None:
        self.setViewportMargins(self.GUTTER_WIDTH, 0, 0, 0)
        rect = self.contentsRect()
        self._gutter.setGeometry(QRect(rect.left(), rect.top(), self.GUTTER_WIDTH, rect.height()))


def _stamp_of(block: QTextBlock) -> str:
    data = block.userData()
    if data is None:
        return ""
    return str(getattr(data, "stamp", "") or "")


def _document_font(pixel_size: int) -> QFont:
    font = QFont()
    font.setFamilies(["Candara", "Calibri", "Segoe UI"])
    font.setStyleHint(QFont.StyleHint.SansSerif)
    font.setPixelSize(pixel_size)
    font.setWeight(QFont.Weight.Normal)
    return font
