from __future__ import annotations

PAPER = "#f6f2ee"
CHROME = "#f1ebe7"
HOVER = "#e9e2dd"
SELECTED = "#e2dad5"
INK = "#1f1d1a"
MUTED = "#6b655f"
COBALT = "#0969da"
COBALT_HOVER = "#0757b8"
CARD = "#fdfbf9"
LINE = "#e6dfda"
LINE_STRONG = "#d6cec8"
PENDING_BG = "#dafbe1"
PENDING_LINE = "#aceebb"
URGENT_BG = "#ffebe9"
URGENT_LINE = "#ffcecb"
DONE_BG = "#eaeef2"
DONE_LINE = "#d0d7de"
PENDING_DOT = "#1a7f37"
URGENT_DOT = "#cf222e"
DONE_DOT = "#8c959f"

UI_FONT = '"Segoe UI","Microsoft YaHei UI",sans-serif'
UI_FAMILIES = ["Segoe UI", "Microsoft YaHei UI"]


def install_font_fallback() -> None:
    from PySide6.QtGui import QFont

    for family in ("Segoe UI", "Segoe UI Variable", "MS Shell Dlg 2"):
        if "Microsoft YaHei UI" not in QFont.substitutes(family):
            QFont.insertSubstitution(family, "Microsoft YaHei UI")


def ui_font(pixel_size: int = 13, weight: int = 400):
    from PySide6.QtGui import QFont

    install_font_fallback()
    font = QFont()
    font.setFamilies(UI_FAMILIES)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    font.setPixelSize(pixel_size)
    font.setWeight(QFont.Weight(weight))
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    return font

SHELL_RADIUS = 10
ROW_RADIUS = 6

STATE_DOT = {"pending": PENDING_DOT, "urgent": URGENT_DOT, "done": DONE_DOT}
STATE_LABEL = {"pending": "普通", "urgent": "紧急", "done": "已完成"}
STATE_PILL = {
    "pending": (PENDING_BG, PENDING_LINE),
    "urgent": (URGENT_BG, URGENT_LINE),
    "done": (DONE_BG, DONE_LINE),
}

_TOOLS = ("QToolButton#addBtn", "QToolButton#pinBtn", "QToolButton#closeDock")


def _each(suffix: str) -> str:
    return ",".join(f"{name}{suffix}" for name in _TOOLS)


def menu_style() -> str:
    return (
        f"QMenu{{background:{CARD};color:{INK};border:1px solid {LINE};"
        f"border-radius:8px;padding:4px;font-size:13px;}}"
        "QMenu::item{padding:6px 24px 6px 10px;border-radius:6px;"
        "background:transparent;}"
        f"QMenu::item:selected{{background:{HOVER};color:{INK};}}"
        f"QMenu::item:disabled{{color:{MUTED};}}"
        f"QMenu::separator{{height:1px;background:{LINE};margin:4px 6px;}}"
        "QMenu::icon{padding-left:6px;}"
    )


def dock_style() -> str:
    return (
        "QWidget#dock{background:transparent;}"
        f"QWidget#shell{{background:{CHROME};color:{INK};border:1px solid {LINE};"
        f"border-radius:{SHELL_RADIUS}px;}}"
        "QWidget#shell[flush='true']{border-radius:0px;}"
        f"QWidget#shell[bubble='true']{{border:1px solid {LINE};}}"
        f"QWidget#detailHost{{background:{PAPER};border:none;}}"
        f"QWidget#rail{{background:{CHROME};border:none;}}"
        f"QWidget#listHost{{background:{CHROME};border:none;}}"
        f"QScrollArea#listScroll{{background:{CHROME};border:none;}}"
        f"QLabel#emptyState{{background:transparent;color:{MUTED};"
        "font-size:13px;padding:28px 20px;}"
        f"QLineEdit#search{{background:transparent;color:{INK};"
        "border:none;border-radius:8px;padding:0 10px;font-size:13px;"
        f"selection-background-color:{COBALT};}}"
        "QLineEdit#search:hover,QLineEdit#search:focus{border:none;}"
        f"{_each('')}{{background:transparent;border:none;border-radius:6px;"
        f"color:{INK};padding:0;}}"
        f"{_each(':hover')}{{background:{HOVER};}}"
        f"{_each(':pressed')},QToolButton#pinBtn:checked{{background:{SELECTED};}}"
        f"{_each(':focus')}{{border:2px solid {COBALT};}}"
        "QWidget#itemCard{}"
        f"QWidget#itemCard:focus{{border:2px solid {COBALT};}}"
        f"QLabel#titleField{{background:transparent;color:{INK};border:none;"
        "padding:0;font-size:14px;}"
        "QScrollBar:vertical{background:transparent;width:8px;margin:2px;}"
        f"QScrollBar::handle:vertical{{background:{LINE_STRONG};border-radius:3px;"
        "min-height:28px;}"
        f"QScrollBar::handle:vertical:hover{{background:{MUTED};}}"
        "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}"
        "QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical{background:none;}"
    )


def document_style() -> str:
    return (
        f"body{{margin:0;background:{PAPER};color:{INK};"
        f"font-family:{UI_FONT};"
        "padding:24px 28px 48px;line-height:1.65}"
        f"a{{color:{COBALT}}}"
        f"a:hover{{color:{COBALT_HOVER}}}"
        f"img{{max-width:100%}}"
        f"pre,code{{background:{CARD};border:1px solid {LINE};border-radius:6px}}"
    )


def wrap_document_html(body: str, extra_css: str = "") -> str:
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<style>{document_style()}{extra_css}</style></head>"
        f"<body>{body}</body></html>"
    )


def card_style(state: str, selected: bool = False) -> str:
    background = SELECTED if selected else "transparent"
    return (
        f"background:{background};border:none;border-radius:{ROW_RADIUS}px;"
        "text-decoration:none;"
    )
