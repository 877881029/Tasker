from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import sqlite3
import time
import uuid

from tasker.paths import attachments_dir

STATES = ("pending", "urgent", "done")


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


class Store:
    def __init__(self, db_file: Path) -> None:
        db_file.parent.mkdir(parents=True, exist_ok=True)
        self._db_file = db_file
        self._conn = sqlite3.connect(str(db_file))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                state TEXT NOT NULL,
                status_pin TEXT NOT NULL,
                body_md TEXT NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                resume_state TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

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
        self._insert(item)
        return item

    def get(self, item_id: str) -> Item | None:
        row = self._conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        return None if row is None else self._from_row(row)

    def save(self, item: Item) -> Item:
        updated = replace(item, updated_at=time.time())
        self._conn.execute(
            """
            UPDATE items SET title=?, state=?, status_pin=?, body_md=?,
                updated_at=?, resume_state=? WHERE id=?
            """,
            (
                updated.title,
                updated.state,
                updated.status_pin,
                updated.body_md,
                updated.updated_at,
                updated.resume_state,
                updated.id,
            ),
        )
        self._conn.commit()
        return updated

    def list_visible(self, query: str = "") -> list[Item]:
        rows = self._conn.execute("SELECT * FROM items").fetchall()
        items = [self._from_row(r) for r in rows]
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

    def _insert(self, item: Item) -> None:
        self._conn.execute(
            """
            INSERT INTO items (
                id, title, state, status_pin, body_md, created_at, updated_at, resume_state
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.id,
                item.title,
                item.state,
                item.status_pin,
                item.body_md,
                item.created_at,
                item.updated_at,
                item.resume_state,
            ),
        )
        self._conn.commit()

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Item:
        return Item(
            id=row["id"],
            title=row["title"],
            state=row["state"],
            status_pin=row["status_pin"],
            body_md=row["body_md"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            resume_state=row["resume_state"],
        )
