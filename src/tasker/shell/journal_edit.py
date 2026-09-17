from __future__ import annotations

from html import escape

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QPalette,
    QResizeEvent,
    QTextBlock,
    QTextBlockFormat,
    QTextBlockUserData,
    QTextCharFormat,
    QTextCursor,
)
from PySide6.QtWidgets import QFrame, QPlainTextEdit, QSizePolicy, QTextBrowser, QWidget

from tasker.theme import COBALT, INK, MUTED, PAPER, wrap_document_html


def journal_document_html(entries: list[tuple[str, str]]) -> str:
    rows: list[str] = []
    for index, (stamp, text) in enumerate(entries):
        klass = " newest" if index == 0 else ""
        lines = escape(text or "").split("\n")
        body = "<br>".join(line if line else "&nbsp;" for line in lines)
        rows.append(
            "<table class='rec' width='100%' cellspacing='0' cellpadding='0'>"
            f"<tr><td class='stamp{klass}' valign='top'>{escape(stamp)}</td>"
            f"<td class='txt' valign='top'>{body}</td></tr></table>"
        )
    extra = (
        "body{padding:8px 12px 32px 0;font-size:16px;line-height:1.72}"
        "table.rec{border:none;margin:0 0 1.15em;width:100%}"
        "td,th{border:none;padding:0}"
        "td.stamp{width:118px;padding-right:12px;text-align:right;"
        f"color:{MUTED};font-size:13px;font-weight:600}}"
        f"td.newest{{color:{COBALT}}}"
        f"td.txt{{color:{INK};font-size:16px;line-height:1.72}}"
    )
    return wrap_document_html("".join(rows), extra_css=extra)


class JournalDocumentView(QTextBrowser):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("journalDocument")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setOpenExternalLinks(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet(
            f"QTextBrowser#journalDocument{{background:{PAPER};border:none;color:{INK};}}"
        )
        pal = self.palette()
        paper = QColor(PAPER)
        ink = QColor(INK)
        for group in (
            QPalette.ColorGroup.Active,
            QPalette.ColorGroup.Inactive,
            QPalette.ColorGroup.Disabled,
        ):
            pal.setColor(group, QPalette.ColorRole.Base, paper)
            pal.setColor(group, QPalette.ColorRole.Window, paper)
            pal.setColor(group, QPalette.ColorRole.Text, ink)
        self.setPalette(pal)
        self.viewport().setPalette(pal)
        self.setAutoFillBackground(True)
        self.viewport().setAutoFillBackground(True)
        self._html = ""

    def set_entries(self, entries: list[tuple[str, str]]) -> None:
        self._html = journal_document_html(entries)
        self.setHtml(self._html)

    def document_html(self) -> str:
        return self._html


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
        self.setStyleSheet(
            f"QPlainTextEdit#journalEditor{{background:{PAPER};color:{INK};border:none;}}"
        )
        self.setFont(_document_font(12))
        self._gutter_font = QFont(self.font())
        if self._gutter_font.pointSize() <= 0:
            self._gutter_font.setPointSize(10)
        else:
            self._gutter_font.setPointSize(max(10, self.font().pointSize() - 2))
        self._gutter_font.setWeight(self.font().weight())
        self._paint_opaque_ink()
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
        self._ink_document()
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
        self._apply_body_format(block)
        cursor = QTextCursor(block)
        cursor.block().setUserData(StampData(stamp) if stamp else None)

    def _apply_body_format(self, block: QTextBlock) -> None:
        fmt = block.blockFormat()
        fmt.setLineHeight(172.0, 1)
        cursor = QTextCursor(block)
        cursor.setBlockFormat(fmt)

    def _paint_opaque_ink(self) -> None:
        pal = self.palette()
        ink = QColor(INK)
        paper = QColor(PAPER)
        for group in (
            QPalette.ColorGroup.Active,
            QPalette.ColorGroup.Inactive,
            QPalette.ColorGroup.Disabled,
        ):
            pal.setColor(group, QPalette.ColorRole.Text, ink)
            pal.setColor(group, QPalette.ColorRole.WindowText, ink)
            pal.setColor(group, QPalette.ColorRole.Base, paper)
            pal.setColor(group, QPalette.ColorRole.Window, paper)
        self.setPalette(pal)
        self.viewport().setPalette(pal)
        self.setAutoFillBackground(True)
        self.viewport().setAutoFillBackground(True)
        ink_fmt = QTextCharFormat()
        ink_fmt.setForeground(ink)
        self.setCurrentCharFormat(ink_fmt)

    def _ink_document(self) -> None:
        block = self.document().begin()
        while block.isValid():
            self._apply_body_format(block)
            block = block.next()
        cursor = QTextCursor(self.document())
        cursor.select(QTextCursor.SelectionType.Document)
        ink_fmt = QTextCharFormat()
        ink_fmt.setForeground(QColor(INK))
        cursor.mergeCharFormat(ink_fmt)

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
        self.viewport().setAutoFillBackground(True)
        self.setViewportMargins(self.GUTTER_WIDTH, 0, 0, 0)
        rect = self.contentsRect()
        self._gutter.setGeometry(QRect(rect.left(), rect.top(), self.GUTTER_WIDTH, rect.height()))


def _stamp_of(block: QTextBlock) -> str:
    data = block.userData()
    if data is None:
        return ""
    return str(getattr(data, "stamp", "") or "")


def _document_font(point_size: int) -> QFont:
    font = QFont()
    font.setFamilies(["Candara", "Calibri", "Segoe UI"])
    font.setStyleHint(QFont.StyleHint.SansSerif)
    font.setPointSize(point_size)
    font.setWeight(QFont.Weight.Normal)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    return font
