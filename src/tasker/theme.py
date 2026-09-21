from __future__ import annotations

PAPER = "#f4efe6"
CHROME = "#ebe4d8"
INK = "#1c1915"
MUTED = "#8a8176"
COBALT = "#2563eb"
COBALT_HOVER = "#1d4ed8"
CARD = "#fffaf2"
LINE = "#e4d9c7"
PENDING_BG = "#ecfdf3"
PENDING_LINE = "#bbf7d0"
URGENT_BG = "#fef2f2"
URGENT_LINE = "#fecaca"
DONE_BG = "#e5e7eb"
DONE_LINE = "#d1d5db"
PENDING_DOT = "#22c55e"
URGENT_DOT = "#ef4444"
DONE_DOT = "#9ca3af"


def dock_style() -> str:
    return (
        "QWidget#dock{background:transparent;}"
        f"QWidget#shell{{background:{PAPER};color:{INK};border:1px solid {LINE};"
        "border-radius:16px;}}"
        "QWidget#shell[flush='true']{border-radius:0px;}"
        f"QWidget#shell[bubble='true']{{border:2px solid {COBALT};}}"
        f"QWidget#detailHost{{background:{PAPER};border:none;}}"
        f"QWidget#rail{{background:{PAPER};border:none;}}"
        f"QWidget#itemCard[selected='true']{{border:2px solid {COBALT};}}"
        f"QWidget#listHost{{background:{PAPER};border:none;}}"
        f"QScrollArea#listScroll{{background:{PAPER};border:none;}}"
        f"QLineEdit#search{{background:transparent;color:{INK};"
        f"border:1px solid {LINE};border-radius:4px;padding:4px 8px;}}"
        f"QLineEdit#search:focus{{border:1px solid {COBALT};}}"
        f"QToolButton#addBtn,QToolButton#pinBtn,QToolButton#closeDock{{background:transparent;border:none;"
        f"color:{COBALT};font-size:18px;font-weight:600;padding:4px 8px;}}"
        f"QToolButton#addBtn:hover,QToolButton#pinBtn:hover,QToolButton#closeDock:hover,"
        f"QToolButton#pinBtn:checked{{background:{CHROME};border-radius:4px;}}"
        f"QWidget#itemCard{{}}"
        f"QLabel#titleField{{background:transparent;color:{INK};border:none;"
        "padding:2px;font-size:15px;}}"
    )


def document_style() -> str:
    return (
        f"body{{margin:0;background:{PAPER};color:{INK};"
        'font-family:Candara,Calibri,"Segoe UI",sans-serif;'
        "padding:24px 28px 48px;line-height:1.72}"
        f"a{{color:{COBALT}}}"
        f"img{{max-width:100%}}"
        f"pre,code{{background:{CARD}}}"
    )


def wrap_document_html(body: str, extra_css: str = "") -> str:
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<style>{document_style()}{extra_css}</style></head>"
        f"<body>{body}</body></html>"
    )


def card_style(state: str) -> str:
    if state == "urgent":
        bg, line = URGENT_BG, URGENT_LINE
    elif state == "done":
        bg, line = DONE_BG, DONE_LINE
    else:
        bg, line = PENDING_BG, PENDING_LINE
    return (
        f"background:{bg};border:1px solid {line};border-radius:8px;"
        "text-decoration:none;"
    )
