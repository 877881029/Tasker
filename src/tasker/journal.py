from __future__ import annotations

from datetime import datetime
import json
import re


STAMP_LINE = re.compile(r"^(\d{6}\.\d{1,2}(?:AM|PM))$")


def stamp_for(when: datetime) -> str:
    hour = when.hour % 12 or 12
    suffix = "AM" if when.hour < 12 else "PM"
    return f"{when:%y%m%d}.{hour}{suffix}"


def parse_journal(body: str) -> list[tuple[str, str]]:
    raw = (body or "").strip("\n")
    if not raw.strip():
        return []
    stripped = raw.strip()
    if stripped.startswith("["):
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError:
            return [("", body)]
        if isinstance(data, list):
            entries: list[tuple[str, str]] = []
            for row in data:
                if isinstance(row, dict):
                    entries.append((str(row.get("stamp", "")), str(row.get("text", ""))))
            return entries
    lines = raw.split("\n")
    if not any(STAMP_LINE.match(line.strip()) for line in lines):
        return [("", body)]
    entries: list[tuple[str, str]] = []
    current_stamp = ""
    current_lines: list[str] = []
    for line in lines:
        match = STAMP_LINE.match(line.strip())
        if match and (not current_lines or current_stamp):
            if current_stamp or any(part.strip() for part in current_lines):
                entries.append((current_stamp, _join_record(current_lines)))
            current_stamp = match.group(1)
            current_lines = []
            continue
        current_lines.append(line)
    if current_stamp or any(part.strip() for part in current_lines):
        entries.append((current_stamp, _join_record(current_lines)))
    return entries


def _join_record(lines: list[str]) -> str:
    return "\n".join(lines).strip("\n")


def dump_journal(entries: list[tuple[str, str]]) -> str:
    blocks: list[str] = []
    for stamp, text in entries:
        body = text.strip("\n")
        if stamp and body:
            blocks.append(f"{stamp}\n\n{body}")
        elif stamp:
            blocks.append(stamp)
        elif body:
            blocks.append(body)
    return "\n\n".join(blocks)


def journal_has_text(body: str) -> bool:
    return any(text.strip() for _stamp, text in parse_journal(body))


def prepend_record(
    entries: list[tuple[str, str]], when: datetime
) -> list[tuple[str, str]]:
    return [(stamp_for(when), "")] + list(entries)


def ensure_current(entries: list[tuple[str, str]], when: datetime) -> list[tuple[str, str]]:
    stamp = stamp_for(when)
    if entries and entries[0][0] == stamp:
        return list(entries)
    return [(stamp, "")] + list(entries)
