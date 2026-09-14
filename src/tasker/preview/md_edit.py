from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QImage
from PySide6.QtCore import QByteArray, QBuffer, QIODevice
from PySide6.QtWidgets import QPlainTextEdit

from tasker.store import Store


class MarkdownEdit(QPlainTextEdit):
    def __init__(self, store: Store, item_id: str, parent=None) -> None:
        super().__init__(parent)
        self._store = store
        self._item_id = item_id

    def set_item_id(self, item_id: str) -> None:
        self._item_id = item_id

    def insertFromMimeData(self, source) -> None:  # type: ignore[override]
        if source.hasImage():
            image = source.imageData()
            if isinstance(image, QImage) and not image.isNull():
                blob = QByteArray()
                buffer = QBuffer(blob)
                buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                image.save(buffer, "PNG")
                path = self._store.write_paste_png(self._item_id, bytes(blob.data()))
                self.insertPlainText(f"![]({path.as_posix()})\n")
                return
        text = source.text().strip()
        if text.startswith("http://") or text.startswith("https://"):
            self.insertPlainText(f"[{text}]({text})")
            return
        super().insertFromMimeData(source)
