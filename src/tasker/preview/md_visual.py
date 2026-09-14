from __future__ import annotations

from markdown_it import MarkdownIt
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView

from tasker.theme import wrap_document_html


def render_markdown(source: str) -> str:
    html = MarkdownIt("commonmark", {"html": False}).render(source or "")
    return wrap_document_html(html)


class TaskerWebPage(QWebEnginePage):
    def acceptNavigationRequest(self, url: QUrl, nav_type, is_main_frame: bool) -> bool:  # type: ignore[override]
        if url.scheme() in {"http", "https"}:
            QDesktopServices.openUrl(url)
            return False
        return super().acceptNavigationRequest(url, nav_type, is_main_frame)


class MarkdownVisual(QWebEngineView):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        page = TaskerWebPage(self)
        settings = page.settings()
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False
        )
        self.setPage(page)

    def set_markdown(self, source: str, base: str | None = None) -> None:
        html = render_markdown(source)
        url = QUrl.fromLocalFile(base) if base else QUrl()
        self.setHtml(html, url)
