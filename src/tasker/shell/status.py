from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import QMenu, QWidget

from tasker.i18n import tr
from tasker.store import Item, Store
from tasker.theme import STATE_LABEL, menu_style, ui_font

STATUS_ORDER = ("pending", "urgent", "done")


def apply_status(store: Store, item_id: str, target: str) -> Item:
    if target not in STATUS_ORDER:
        raise ValueError(target)
    item = store.get(item_id)
    if item is None:
        raise KeyError(item_id)
    if target == "done":
        return store.set_done(item_id, True)
    if item.state == "done":
        item = store.set_done(item_id, False)
    if item.state != target:
        item = store.cycle_color(item_id)
    return item


def style_menu(menu: QMenu) -> QMenu:
    menu.setWindowFlags(
        menu.windowFlags()
        | Qt.WindowType.FramelessWindowHint
        | Qt.WindowType.NoDropShadowWindowHint
    )
    menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    menu.setFont(ui_font(13))
    menu.setStyleSheet(menu_style())
    return menu


def build_status_menu(
    current: str, on_pick: Callable[[str], None], parent: QWidget | None = None
) -> QMenu:
    menu = style_menu(QMenu(parent))
    menu.setObjectName("statusMenu")
    group = QActionGroup(menu)
    group.setExclusive(True)
    for state in STATUS_ORDER:
        action = QAction(tr(STATE_LABEL[state]), menu)
        action.setCheckable(True)
        action.setChecked(state == current)
        action.setData(state)
        action.triggered.connect(lambda _checked=False, s=state: on_pick(s))
        group.addAction(action)
        menu.addAction(action)
    return menu
