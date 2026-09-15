from __future__ import annotations

from datetime import datetime
import json


def stamp_for(when: datetime) -> str:
    hour = when.hour % 12 or 12
    suffix = "AM" if when.hour < 12 else "PM"
    return f"{when:%y%m%d}.{hour}{suffix}"


def parse_journal(body: str) -> list[tuple[str, str]]:
    raw = (body or "").strip()
    if not raw:
        return []
    if raw.startswith("["):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return [("", body)]
        if isinstance(data, list):
            entries: list[tuple[str, str]] = []
            for row in data:
                if isinstance(row, dict):
                    entries.append((str(row.get("stamp", "")), str(row.get("text", ""))))
            return entries
    return [("", body)]


def dump_journal(entries: list[tuple[str, str]]) -> str:
    payload = [{"stamp": stamp, "text": text} for stamp, text in entries]
    if not payload:
        return ""
    return json.dumps(payload, ensure_ascii=False)


def journal_has_text(body: str) -> bool:
    return any(text.strip() for _stamp, text in parse_journal(body))


def ensure_current(entries: list[tuple[str, str]], when: datetime) -> list[tuple[str, str]]:
    stamp = stamp_for(when)
    if entries and entries[0][0] == stamp:
        return list(entries)
    return [(stamp, "")] + list(entries)
