from __future__ import annotations

from html import escape

from PySide6.QtCore import QEventLoop, QRect, QSize, Qt, QTimer, QUrl
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
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QFrame, QPlainTextEdit, QSizePolicy, QWidget

from tasker.preview.md_visual import TaskerWebPage
from tasker.theme import COBALT, INK, MUTED, PAPER, wrap_document_html


_READ_WRITE_STATE_JS = """
(() => {
  function useful(s) {
    return String(s || '').replace(/[\\s\\u00a0]/g, '');
  }
  function rowText(node) {
    if (!node) return '';
    var html = node.innerHTML || '';
    var fromHtml = html
      .replace(/&nbsp;/gi, ' ')
      .replace(/<br\\s*\\/?>/gi, '\\n')
      .replace(/<\\/div>/gi, '\\n')
      .replace(/<div[^>]*>/gi, '')
      .replace(/<\\/p>/gi, '\\n')
      .replace(/<p[^>]*>/gi, '')
      .replace(/<[^>]+>/g, '')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&amp;/g, '&');
    var laid = node.innerText || '';
    var content = node.textContent || '';
    var raw = useful(laid) ? laid : (useful(fromHtml) ? fromHtml : content);
    return String(raw).replace(/\\u00a0/g, ' ').replace(/\\n+$/, '');
  }
  var stamps = Array.from(document.querySelectorAll('.stamp'));
  var texts = Array.from(document.querySelectorAll('.txt'));
  var live = stamps.map(function (stamp, i) {
    return [stamp.innerText.trim(), rowText(texts[i])];
  });
  var snap = window._journalRows;
  var liveHas = live.some(function (row) { return useful(row[1]); });
  var rows = liveHas ? live : (Array.isArray(snap) ? snap : live);
  return [!!window._journalDirty, rows];
})()
"""

_WRITE_BOOTSTRAP_JS = """
window._journalDirty=false;
window._journalRows=null;
document.addEventListener('input',function(){
  window._journalDirty=true;
  window._journalRows=(function(){
    var stamps=Array.from(document.querySelectorAll('.stamp'));
    var texts=Array.from(document.querySelectorAll('.txt'));
    return stamps.map(function(stamp,i){
      var node=texts[i];
      var raw=node?(node.innerText||node.textContent||node.innerHTML||''):'';
      return [stamp.innerText.trim(), String(raw).replace(/<br\\s*\\/?>/gi,'\\n').replace(/<[^>]+>/g,'').replace(/\\u00a0/g,' ').replace(/\\n+$/,'')];
    });
  })();
},true);
document.addEventListener('keydown',function(e){
  if((e.ctrlKey||e.metaKey)&&(e.key==='s'||e.key==='S')){e.preventDefault();e.stopPropagation();}
},true);
var _el=document.querySelector('.txt');if(_el)_el.focus();
"""


def parse_write_state(payload: object) -> tuple[bool, list[tuple[str, str]]] | None:
    if payload is None or not isinstance(payload, (list, tuple)) or len(payload) < 2:
        return None
    dirty = bool(payload[0])
    rows = payload[1]
    if not isinstance(rows, list):
        return None
    found: list[tuple[str, str]] = []
    for row in rows:
        if not isinstance(row, (list, tuple)) or len(row) < 2:
            continue
        found.append((str(row[0]), str(row[1])))
    return dirty, found


def journal_document_html(
    entries: list[tuple[str, str]], *, writable: bool = False
) -> str:
    cells: list[str] = []
    edit = ' contenteditable="true" spellcheck="false"' if writable else ""
    for index, (stamp, text) in enumerate(entries):
        klass = " newest" if index == 0 else ""
        lines = escape(text or "").split("\n")
        if text:
            body = "<br>".join(line if line else "&nbsp;" for line in lines)
        else:
            body = "<br>"
        cells.append(
            f'<div class="stamp{klass}">{escape(stamp)}</div>'
            f'<div class="txt"{edit}>{body}</div>'
        )
    extra = (
        "body{padding:8px 20px 32px 12px;font-size:16px;line-height:1.72;"
        'font-family:Candara,Calibri,"Segoe UI",sans-serif}'
        ".log{display:grid;grid-template-columns:7.75rem minmax(0,1fr);"
        "column-gap:12px;row-gap:1.15em;align-items:start}"
        f".stamp{{text-align:right;color:{MUTED};font-size:13px;font-weight:600;"
        "line-height:1.72;white-space:nowrap;-webkit-user-select:none;"
        "user-select:none}}"
        f".stamp.newest{{color:{COBALT}}}"
        f".txt{{color:{INK};font-size:16px;line-height:1.72;min-width:0;"
        "overflow-wrap:anywhere}}"
        f".txt[contenteditable]{{outline:none;caret-color:{INK};min-height:1.72em}}"
    )
    script = ""
    if writable:
        script = f"<script>{_WRITE_BOOTSTRAP_JS}</script>"
    return wrap_document_html(
        f'<div class="log">{"".join(cells)}</div>{script}', extra_css=extra
    )


class JournalDocumentView(QWebEngineView):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("journalDocument")
        self.setMinimumSize(0, 0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        page = TaskerWebPage(self)
        page.setBackgroundColor(QColor(PAPER))
        settings = page.settings()
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False
        )
        settings.setFontFamily(QWebEngineSettings.FontFamily.StandardFont, "Candara")
        settings.setFontFamily(QWebEngineSettings.FontFamily.SansSerifFont, "Candara")
        settings.setFontSize(QWebEngineSettings.FontSize.DefaultFontSize, 16)
        self.setPage(page)
        self._html = ""
        self._writable = False
        self._pending_focus = False
        self._ready = False
        self._live_rows: list[tuple[str, str]] | None = None
        self._poll = QTimer(self)
        self._poll.setInterval(120)
        self._poll.timeout.connect(self._poll_rows)
        self.loadFinished.connect(self._on_loaded)

    def set_entries(
        self, entries: list[tuple[str, str]], *, writable: bool = False
    ) -> None:
        self._poll.stop()
        self._live_rows = None
        self._writable = writable
        self._pending_focus = writable
        self._ready = False
        self._html = journal_document_html(entries, writable=writable)
        self.setHtml(self._html, QUrl())

    def document_html(self) -> str:
        return self._html

    def live_rows(self) -> list[tuple[str, str]] | None:
        if not self._live_rows:
            return None
        if not any((text or "").strip() for _stamp, text in self._live_rows):
            return None
        return list(self._live_rows)

    def read_write_state(self) -> tuple[bool, list[tuple[str, str]]] | None:
        if not self._writable:
            return None
        live = self.live_rows()
        if live is not None:
            return True, live
        captured: list[object] = []
        loop = QEventLoop()

        def _done(value: object) -> None:
            captured.append(value)
            loop.quit()

        self.page().runJavaScript(_READ_WRITE_STATE_JS, _done)
        QTimer.singleShot(1500, loop.quit)
        loop.exec()
        if not captured:
            return None
        parsed = parse_write_state(captured[0])
        if parsed is None:
            return None
        dirty, found = parsed
        if any((text or "").strip() for _stamp, text in found):
            self._live_rows = found
        return dirty, found

    def _poll_rows(self) -> None:
        if not self._writable:
            self._poll.stop()
            return
        self.page().runJavaScript(_READ_WRITE_STATE_JS, self._accept_poll)

    def _accept_poll(self, payload: object) -> None:
        parsed = parse_write_state(payload)
        if parsed is None:
            return
        _dirty, rows = parsed
        if any((text or "").strip() for _stamp, text in rows):
            self._live_rows = rows

    def _on_loaded(self, ok: bool) -> None:
        self._ready = bool(ok)
        if not ok or not self._writable:
            return
        focus = ""
        if self._pending_focus:
            self._pending_focus = False
            focus = "var el=document.querySelector('.txt');if(el){el.focus();}"
        self.page().runJavaScript(
            "window._journalDirty=window._journalDirty||false;"
            "document.addEventListener('input',function(){window._journalDirty=true;},true);"
            "document.addEventListener('keydown',function(e){"
            "if((e.ctrlKey||e.metaKey)&&(e.key==='s'||e.key==='S'))"
            "{e.preventDefault();e.stopPropagation();}},true);"
            + focus
        )
        self._poll.start()
        self._poll_rows()


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
            f"QPlainTextEdit#journalEditor{{background:{PAPER};color:{INK};border:none;font-size:16px;}}"
        )
        self.setFont(_document_font(16))
        self.document().setDefaultFont(self.font())
        self._gutter_font = QFont(self.font())
        self._gutter_font.setPixelSize(13)
        self._gutter_font.setWeight(QFont.Weight.DemiBold)
        self._paint_opaque_ink()
        self._gutter = _StampGutter(self)
        self.blockCountChanged.connect(lambda _n: self._sync_gutter())
        self.updateRequest.connect(self._on_update_request)
        self._sync_gutter()

    def gutter(self) -> QWidget:
        return self._gutter

    def gutter_font(self) -> QFont:
        return QFont(self._gutter_font)

    def sync_surface(self) -> None:
        self._paint_opaque_ink()
        self._sync_gutter()

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
        self._paint_opaque_ink()
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
        ink_fmt.setFont(self.font())
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


def _document_font(pixel_size: int) -> QFont:
    font = QFont()
    font.setFamilies(["Candara", "Calibri", "Segoe UI"])
    font.setStyleHint(QFont.StyleHint.SansSerif)
    font.setPixelSize(pixel_size)
    font.setWeight(QFont.Weight.Normal)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    return font
