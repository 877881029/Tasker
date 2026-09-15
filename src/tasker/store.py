from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import json
import sqlite3
import time
import uuid

from tasker.journal import dump_journal, journal_has_text, parse_journal
from tasker.paths import attachments_dir, data_dir, tasks_dir

STATES = ("pending", "urgent", "done")


def is_empty_note(item: Item) -> bool:
    return (
        not item.title.strip()
        and not item.status_pin.strip()
        and not journal_has_text(item.body_md)
    )


def is_blank_draft(item: Item) -> bool:
    return item.state == "pending" and is_empty_note(item)


@dataclass(frozen=True)
class Item:
    id: str
    title: str
    state: str
    status_pin: str
    body_md: str
    created_at: float
    updated_at: float
    resume_state: str


def _yaml_scalar(value: str) -> str:
    if value == "" or any(char in value for char in ":#\n\"'"):
        return json.dumps(value, ensure_ascii=False)
    return value


def _unquote(value: str) -> str:
    text = value.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return text[1:-1]
        return str(parsed)
    return text


def _parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text
    rest = text[3:].lstrip("\n")
    end = rest.find("\n---")
    if end < 0:
        return {}, text
    header = rest[:end]
    body = rest[end + 4 :].lstrip("\n")
    meta: dict[str, str] = {}
    for line in header.splitlines():
        if ":" not in line:
            continue
        key, raw = line.split(":", 1)
        meta[key.strip()] = _unquote(raw.strip())
    return meta, body


def _render_task(item: Item) -> str:
    header = (
        "---\n"
        f"title: {_yaml_scalar(item.title)}\n"
        f"state: {item.state}\n"
        f"resume_state: {item.resume_state}\n"
        f"created_at: {item.created_at}\n"
        f"updated_at: {item.updated_at}\n"
        "---\n"
    )
    body = dump_journal(parse_journal(item.body_md)) if item.body_md.strip() else ""
    if body:
        return header + "\n" + body + "\n"
    return header + "\n"


def _pin_from_body(body: str) -> str:
    entries = parse_journal(body)
    if not entries:
        return ""
    text = entries[0][1].strip()
    return text.splitlines()[0] if text else ""


def migrate_sqlite_if_needed(root: Path) -> None:
    db_file = root / "tasker.sqlite"
    task_root = root / "tasks"
    if not db_file.is_file():
        return
    if task_root.exists() and any(task_root.glob("*.md")):
        return
    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("SELECT * FROM items").fetchall()
    except sqlite3.Error:
        conn.close()
        return
    task_root.mkdir(parents=True, exist_ok=True)
    for row in rows:
        body = dump_journal(parse_journal(row["body_md"]))
        item = Item(
            id=row["id"],
            title=row["title"],
            state=row["state"],
            status_pin=row["status_pin"],
            body_md=body,
            created_at=float(row["created_at"]),
            updated_at=float(row["updated_at"]),
            resume_state=row["resume_state"],
        )
        (task_root / f"{item.id}.md").write_text(_render_task(item), encoding="utf-8")
    conn.close()


class Store:
    def __init__(self, root: Path | None = None) -> None:
        path = Path(root) if root is not None else data_dir()
        if path.suffix == ".sqlite":
            path = path.parent
        self._root = path
        self._root.mkdir(parents=True, exist_ok=True)
        migrate_sqlite_if_needed(self._root)
        self._tasks = self._root / "tasks"
        self._tasks.mkdir(parents=True, exist_ok=True)

    def _path_for(self, item_id: str) -> Path:
        return self._tasks / f"{item_id}.md"

    def _read(self, path: Path) -> Item | None:
        if not path.is_file():
            return None
        text = path.read_text(encoding="utf-8")
        meta, body = _parse_front_matter(text)
        body = body.strip("\n")
        item_id = path.stem
        created = float(meta.get("created_at") or path.stat().st_mtime)
        updated = float(meta.get("updated_at") or path.stat().st_mtime)
        state = meta.get("state") or "pending"
        return Item(
            id=item_id,
            title=meta.get("title") or "",
            state=state,
            status_pin=_pin_from_body(body),
            body_md=body,
            created_at=created,
            updated_at=updated,
            resume_state=meta.get("resume_state") or state,
        )

    def create(self) -> Item:
        now = time.time()
        item = Item(
            id=str(uuid.uuid4()),
            title="",
            state="pending",
            status_pin="",
            body_md="",
            created_at=now,
            updated_at=now,
            resume_state="pending",
        )
        self._path_for(item.id).write_text(_render_task(item), encoding="utf-8")
        return item

    def delete(self, item_id: str) -> None:
        path = self._path_for(item_id)
        if path.exists():
            path.unlink()

    def collapse_blank_drafts(self) -> Item | None:
        empties = [item for item in self.list_visible() if is_empty_note(item)]
        if not empties:
            return None
        keep = max(empties, key=lambda item: item.updated_at)
        for extra in empties:
            if extra.id != keep.id:
                self.delete(extra.id)
        return keep

    def ensure_draft(self) -> Item:
        existing = self.collapse_blank_drafts()
        if existing is not None:
            return existing
        return self.create()

    def get(self, item_id: str) -> Item | None:
        return self._read(self._path_for(item_id))

    def save(self, item: Item) -> Item:
        updated = replace(
            item,
            updated_at=time.time(),
            status_pin=_pin_from_body(item.body_md),
            body_md=dump_journal(parse_journal(item.body_md)) if item.body_md.strip() else "",
        )
        self._path_for(updated.id).write_text(_render_task(updated), encoding="utf-8")
        return updated

    def list_visible(self, query: str = "") -> list[Item]:
        items = [
            item
            for path in self._tasks.glob("*.md")
            if (item := self._read(path)) is not None
        ]
        needle = query.strip().casefold()
        if needle:
            items = [
                item
                for item in items
                if needle in item.title.casefold() or needle in item.body_md.casefold()
            ]
        rank = {"urgent": 0, "pending": 1, "done": 2}
        items.sort(key=lambda i: (rank.get(i.state, 9), -i.updated_at))
        return items

    def cycle_color(self, item_id: str) -> Item:
        item = self.get(item_id)
        if item is None:
            raise KeyError(item_id)
        if item.state == "done":
            return item
        nxt = "urgent" if item.state == "pending" else "pending"
        return self.save(replace(item, state=nxt, resume_state=nxt))

    def set_done(self, item_id: str, done: bool) -> Item:
        item = self.get(item_id)
        if item is None:
            raise KeyError(item_id)
        if done:
            if item.state == "done":
                return item
            return self.save(replace(item, resume_state=item.state, state="done"))
        if item.state != "done":
            return item
        return self.save(replace(item, state=item.resume_state))

    def write_paste_png(self, item_id: str, data: bytes) -> Path:
        folder = attachments_dir(item_id)
        path = folder / f"{uuid.uuid4().hex}.png"
        path.write_bytes(data)
        return path
