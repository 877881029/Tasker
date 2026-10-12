from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta

from PySide6.QtCore import QDate, QDateTime, QTime
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QDateTimeEdit,
    QLabel,
    QMenu,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

from tasker.theme import CARD, COBALT, INK, LINE_STRONG, MUTED, ui_font

SOON = timedelta(hours=24)


def format_countdown(left: timedelta) -> str:
    minutes = max(0, int(left.total_seconds()) // 60)
    days, rest = divmod(minutes, 24 * 60)
    hours, mins = divmod(rest, 60)
    return f"{days:02d}d-{hours:02d}h-{mins:02d}m"


def countdown_text(deadline: datetime, now: datetime | None = None) -> tuple[str, str]:
    """Return the countdown label and its tone: normal, soon or overdue."""
    moment = now or datetime.now()
    left = deadline - moment
    if left.total_seconds() < 0:
        return f"超期 {format_countdown(-left)}", "overdue"
    return format_countdown(left), "soon" if left <= SOON else "normal"


def deadline_label(deadline: datetime, now: datetime | None = None) -> str:
    moment = now or datetime.now()
    if deadline.year == moment.year:
        return deadline.strftime("%m-%d %H:%M")
    return deadline.strftime("%Y-%m-%d %H:%M")


def deadline_presets(now: datetime | None = None) -> list[tuple[str, datetime]]:
    moment = (now or datetime.now()).replace(second=0, microsecond=0)
    day = moment.replace(hour=0, minute=0)
    options: list[tuple[str, datetime]] = []
    today = day.replace(hour=18)
    if today > moment:
        options.append(("今天 18:00", today))
    options.append(("明天 18:00", (day + timedelta(days=1)).replace(hour=18)))
    options.append(("3 天后 18:00", (day + timedelta(days=3)).replace(hour=18)))
    monday = day + timedelta(days=7 - day.weekday())
    options.append(("下周一 09:00", monday.replace(hour=9)))
    return options


def to_qdatetime(value: datetime) -> QDateTime:
    return QDateTime(
        QDate(value.year, value.month, value.day), QTime(value.hour, value.minute)
    )


def from_qdatetime(value: QDateTime) -> datetime:
    date, clock = value.date(), value.time()
    return datetime(date.year(), date.month(), date.day(), clock.hour(), clock.minute())


def _custom_editor(
    current: datetime | None, on_pick: Callable[[datetime], None], menu: QMenu
) -> QWidgetAction:
    box = QWidget(menu)
    box.setObjectName("deadlineCustom")
    layout = QVBoxLayout(box)
    layout.setContentsMargins(10, 4, 10, 6)
    layout.setSpacing(4)
    hint = QLabel("自定义：滚轮或方向键调整，回车确定")
    hint.setStyleSheet(f"color:{MUTED};font-size:12px;background:transparent;")
    edit = QDateTimeEdit(box)
    edit.setObjectName("deadlineEdit")
    edit.setDisplayFormat("yyyy-MM-dd HH:mm")
    edit.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
    edit.setCurrentSection(QDateTimeEdit.Section.DaySection)
    edit.setFont(ui_font(13))
    edit.setMinimumWidth(180)
    fallback = (datetime.now() + timedelta(days=1)).replace(
        hour=18, minute=0, second=0, microsecond=0
    )
    edit.setDateTime(to_qdatetime(current or fallback))
    edit.setStyleSheet(
        f"QDateTimeEdit#deadlineEdit{{background:{CARD};color:{INK};"
        f"border:1px solid {LINE_STRONG};border-radius:6px;padding:4px 8px;"
        f"selection-background-color:{COBALT};}}"
        f"QDateTimeEdit#deadlineEdit:focus{{border:2px solid {COBALT};padding:3px 7px;}}"
    )

    def commit() -> None:
        on_pick(from_qdatetime(edit.dateTime()))
        menu.close()

    edit.editingFinished.connect(lambda: commit() if edit.hasFocus() else None)
    layout.addWidget(hint)
    layout.addWidget(edit)
    action = QWidgetAction(menu)
    action.setDefaultWidget(box)
    menu.deadline_edit = edit  # type: ignore[attr-defined]
    return action


def build_deadline_menu(
    current: datetime | None,
    on_pick: Callable[[datetime | None], None],
    parent: QWidget | None = None,
    now: datetime | None = None,
) -> QMenu:
    from tasker.shell.status import style_menu

    menu = style_menu(QMenu(parent))
    menu.setObjectName("deadlineMenu")
    for label, when in deadline_presets(now):
        action = menu.addAction(label)
        action.setData(when)
        action.setCheckable(True)
        action.setChecked(current == when)
        action.triggered.connect(lambda _checked=False, w=when: on_pick(w))
    menu.addSeparator()
    menu.addAction(_custom_editor(current, on_pick, menu))
    menu.addSeparator()
    clear = menu.addAction("清除 DDL")
    clear.setEnabled(current is not None)
    clear.triggered.connect(lambda _checked=False: on_pick(None))
    return menu
