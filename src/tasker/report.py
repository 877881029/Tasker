from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import date, datetime, timedelta

from tasker.i18n import tr
from tasker.deadline import deadline_label
from tasker.journal import STAMP_LINE, parse_journal
from tasker.store import Item

GROUPS = (("urgent", "紧急"), ("pending", "普通"), ("done", "已完成"))
_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_STAMP = re.compile(r"^(\d{2})(\d{2})(\d{2})\.(\d{1,2})(AM|PM)$")


def summary_line(text: str) -> str:
    for raw in (text or "").splitlines():
        line = _IMAGE.sub(tr("[图片]"), raw).strip()
        if line:
            return line
    return ""


def stamp_date(stamp: str) -> date | None:
    match = _STAMP.match(stamp.strip())
    if match is None:
        return None
    yy, mm, dd = (int(part) for part in match.group(1, 2, 3))
    try:
        return date(2000 + yy, mm, dd)
    except ValueError:
        return None


def week_bounds(now: datetime) -> tuple[date, date]:
    monday = now.date() - timedelta(days=now.weekday())
    return monday, monday + timedelta(days=6)


def _entry_lines(stamp: str, text: str, when: date) -> list[str]:
    match = _STAMP.match(stamp.strip())
    hour = f"{match.group(4)}{match.group(5)}" if match else ""
    rows = [_IMAGE.sub(tr("[图片]"), line).rstrip() for line in text.strip("\n").splitlines()]
    rows = [row for row in rows if row.strip()]
    if not rows:
        return []
    head = f"- {when:%m-%d} {hour}：{rows[0].strip()}".rstrip()
    return [head] + [f"  {row}" for row in rows[1:]]


def weekly_report(items: Iterable[Item], now: datetime | None = None) -> tuple[str, int]:
    moment = now or datetime.now()
    start, end = week_bounds(moment)
    sections: dict[str, list[str]] = {state: [] for state, _label in GROUPS}
    count = 0
    for item in items:
        lines: list[str] = []
        for stamp, text in parse_journal(item.body_md):
            if not STAMP_LINE.match(stamp.strip()):
                continue
            when = stamp_date(stamp)
            if when is None or not (start <= when <= moment.date()):
                continue
            lines.extend(_entry_lines(stamp, text, when))
        if not lines or item.state not in sections:
            continue
        title = item.title.strip() or tr("无标题")
        if item.state == "urgent" and item.deadline is not None:
            title += f"（DDL {deadline_label(item.deadline, moment)}）"
        sections[item.state].extend([f"### {title}", *lines, ""])
        count += 1
    out = [tr("# 周报 {start} ~ {end}", start=f"{start:%Y-%m-%d}", end=f"{end:%Y-%m-%d}"), ""]
    if count == 0:
        out.append(tr("本周暂无记录"))
        return "\n".join(out) + "\n", 0
    for state, label in GROUPS:
        if sections[state]:
            out.append(f"## {tr(label)}")
            out.extend(sections[state])
    return "\n".join(out).rstrip("\n") + "\n", count
