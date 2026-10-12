from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta

from tasker.deadline import countdown_text, deadline_label
from tasker.store import Item

SOON_WINDOW = timedelta(hours=1)


@dataclass(frozen=True)
class Reminder:
    kind: str
    title: str
    body: str
    item_id: str | None = None


def _due(item: Item) -> datetime | None:
    return item.deadline if item.state == "urgent" else None


def overdue_count(items: Iterable[Item], now: datetime) -> int:
    return sum(1 for item in items if (due := _due(item)) is not None and due <= now)


def badge_text(count: int) -> str:
    if count <= 0:
        return ""
    return "9+" if count > 9 else str(count)


def _name(item: Item) -> str:
    return item.title.strip() or "无标题"


class ReminderTracker:
    def __init__(self) -> None:
        self._sent: set[tuple[str, str, str]] = set()
        self._primed = False

    def check(self, items: Iterable[Item], now: datetime) -> list[Reminder]:
        out: list[Reminder] = []
        overdue_at_start = 0
        for item in items:
            due = _due(item)
            if due is None:
                continue
            stamp = due.isoformat()
            soon_key = (item.id, "soon", stamp)
            over_key = (item.id, "overdue", stamp)
            if due <= now:
                self._sent.add(soon_key)
                if over_key in self._sent:
                    continue
                self._sent.add(over_key)
                if not self._primed:
                    overdue_at_start += 1
                    continue
                out.append(
                    Reminder(
                        "overdue",
                        "已超期",
                        f"{_name(item)} · DDL {deadline_label(due, now)}",
                        item.id,
                    )
                )
            elif due - now <= SOON_WINDOW and soon_key not in self._sent:
                self._sent.add(soon_key)
                left, _tone = countdown_text(due, now)
                out.append(Reminder("soon", "即将截止", f"{_name(item)} · 剩余 {left}", item.id))
        if not self._primed and overdue_at_start:
            out.insert(
                0,
                Reminder("summary", "Tasker", f"有 {overdue_at_start} 个任务已超期"),
            )
        self._primed = True
        return out
