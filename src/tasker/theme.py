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
        f"background:{bg};border:1px solid {line};border-radius:6px;"
        "text-decoration:none;"
    )
