from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWebEngineCore import QWebEnginePage


class TaskerWebPage(QWebEnginePage):
    def acceptNavigationRequest(self, url: QUrl, nav_type, is_main_frame: bool) -> bool:  # type: ignore[override]
        if url.scheme() in {"http", "https"}:
            QDesktopServices.openUrl(url)
            return False
        return super().acceptNavigationRequest(url, nav_type, is_main_frame)
