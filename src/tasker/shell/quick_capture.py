from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QEvent, QPoint, Qt
from PySide6.QtGui import QColor, QGuiApplication, QKeyEvent, QPalette
from PySide6.QtWidgets import QFrame, QLabel, QLineEdit, QVBoxLayout, QWidget

from tasker.i18n import tr
from tasker.theme import CARD, COBALT, INK, LINE_STRONG, MUTED, ui_font

HINT = "回车保存 · Esc 取消 · 以 ! 开头设为紧急"


def parse_capture(text: str) -> tuple[str, bool]:
    title = (text or "").strip()
    urgent = False
    if title[:1] in {"!", "！"}:
        urgent = True
        title = title[1:].strip()
    return title, urgent


class CaptureLineEdit(QLineEdit):
    def __init__(self, on_submit: Callable[[], None], on_cancel: Callable[[], None]) -> None:
        super().__init__()
        self._on_submit = on_submit
        self._on_cancel = on_cancel

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in {Qt.Key.Key_Return, Qt.Key.Key_Enter}:
            self._on_submit()
            event.accept()
            return
        if event.key() == Qt.Key.Key_Escape:
            self._on_cancel()
            event.accept()
            return
        super().keyPressEvent(event)


class QuickCapture(QWidget):
    WIDTH = 480

    def __init__(self, on_create: Callable[[str, bool], None], parent=None) -> None:
        super().__init__(parent)
        self._on_create = on_create
        self.setObjectName("quickCapture")
        self.setWindowTitle(tr("快速记录"))
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFont(ui_font(13))
        self.frame = QFrame(self)
        self.frame.setObjectName("captureFrame")
        self.frame.setStyleSheet(
            f"QFrame#captureFrame{{background:{CARD};border:1px solid {LINE_STRONG};"
            "border-radius:8px;}"
        )
        self.edit = CaptureLineEdit(self.submit, self.cancel)
        self.edit.setObjectName("captureEdit")
        self.edit.setFrame(False)
        self.edit.setPlaceholderText(tr("记一件事…"))
        self.edit.setAccessibleName(tr("快速记录任务标题"))
        self.edit.setFont(ui_font(16))
        self.edit.setMinimumHeight(36)
        self.edit.setStyleSheet(
            f"QLineEdit#captureEdit{{background:transparent;color:{INK};border:none;"
            f"padding:0 4px;selection-background-color:{COBALT};}}"
        )
        palette = self.edit.palette()
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(MUTED))
        self.edit.setPalette(palette)
        self.hint = QLabel(tr(HINT))
        self.hint.setObjectName("captureHint")
        self.hint.setStyleSheet(f"color:{MUTED};font-size:12px;padding:0 4px;")
        inner = QVBoxLayout(self.frame)
        inner.setContentsMargins(12, 10, 12, 10)
        inner.setSpacing(4)
        inner.addWidget(self.edit)
        inner.addWidget(self.hint)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.frame)
        self.setFixedWidth(self.WIDTH)

    def popup(self) -> None:
        screen = QGuiApplication.screenAt(self.cursor().pos()) or QGuiApplication.primaryScreen()
        avail = screen.availableGeometry()
        self.adjustSize()
        x = avail.x() + (avail.width() - self.width()) // 2
        y = avail.y() + avail.height() // 4
        self.move(QPoint(x, y))
        self.edit.clear()
        self.show()
        self.raise_()
        self.activateWindow()
        self.edit.setFocus(Qt.FocusReason.ShortcutFocusReason)

    def submit(self) -> None:
        title, urgent = parse_capture(self.edit.text())
        self.hide()
        self.edit.clear()
        if title:
            self._on_create(title, urgent)

    def cancel(self) -> None:
        self.edit.clear()
        self.hide()

    def event(self, event) -> bool:
        if event.type() == QEvent.Type.WindowDeactivate and self.isVisible():
            self.cancel()
        return super().event(event)
