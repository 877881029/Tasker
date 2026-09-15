from dataclasses import replace

from tasker.store import Store, is_blank_draft, is_empty_note


def test_create_pending_empty_title(tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path / "tasker.sqlite")
    item = store.create()
    assert item.title == ""
    assert item.state == "pending"
    assert item.status_pin == ""
    assert item.body_md == ""
    loaded = store.get(item.id)
    assert loaded is not None
    assert loaded.id == item.id
    assert loaded.state == "pending"


def test_cycle_color_skips_done(tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path / "tasker.sqlite")
    item = store.create()
    urgent = store.cycle_color(item.id)
    assert urgent.state == "urgent"
    pending = store.cycle_color(urgent.id)
    assert pending.state == "pending"
    done = store.set_done(pending.id, True)
    assert done.state == "done"
    assert store.cycle_color(done.id).state == "done"


def test_uncheck_done_restores_urgent(tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path / "tasker.sqlite")
    item = store.cycle_color(store.create().id)
    done = store.set_done(item.id, True)
    assert done.state == "done"
    restored = store.set_done(done.id, False)
    assert restored.state == "urgent"


def test_search_filters_title_and_body(tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path / "tasker.sqlite")
    pdf = store.save(replace(store.create(), title="PDF 默认应用"))
    store.save(replace(store.create(), title="setup", body_md="no match here"))
    hits = store.list_visible("PDF")
    assert [i.id for i in hits] == [pdf.id]


def test_list_order_urgent_pending_done(tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path / "tasker.sqlite")
    pending = store.create()
    urgent = store.cycle_color(store.create().id)
    done = store.set_done(store.create().id, True)
    ordered = store.list_visible()
    assert [i.id for i in ordered] == [urgent.id, pending.id, done.id]


def test_ensure_draft_reuses_and_collapses_blanks(tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path / "tasker.sqlite")
    a = store.create()
    b = store.create()
    titled = store.save(replace(store.create(), title="实事项"))
    urgent_empty = store.cycle_color(store.create().id)
    assert is_blank_draft(a) and is_blank_draft(b)
    assert not is_blank_draft(titled)
    assert is_empty_note(urgent_empty)
    kept = store.ensure_draft()
    ids = {i.id for i in store.list_visible()}
    assert kept.id in {a.id, b.id, urgent_empty.id}
    assert titled.id in ids
    empties = [i for i in store.list_visible() if is_empty_note(i)]
    assert len(empties) == 1
    again = store.ensure_draft()
    assert again.id == kept.id
    store.save(replace(kept, title="已写"))
    created = store.ensure_draft()
    assert created.id != kept.id


def test_write_paste_png(tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path / "tasker.sqlite")
    item = store.create()
    path = store.write_paste_png(item.id, b"\x89PNG")
    assert path.exists()
    assert path.parent.name == item.id
    assert path.read_bytes().startswith(b"\x89PNG")


def test_create_writes_md_not_sqlite(tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path)
    item = store.create()
    md = tmp_path / "tasks" / f"{item.id}.md"
    assert md.is_file()
    assert "state: pending" in md.read_text(encoding="utf-8")
    assert not (tmp_path / "tasker.sqlite").exists()


def test_delete_keeps_foreign_image(tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path)
    item = store.create()
    foreign = tmp_path / "photos" / "keep.png"
    foreign.parent.mkdir()
    foreign.write_bytes(b"img")
    store.save(replace(item, body_md=f"260915.3PM\n\n![]({foreign.as_posix()})"))
    store.delete(item.id)
    assert not (tmp_path / "tasks" / f"{item.id}.md").exists()
    assert foreign.exists()


def test_migrate_sqlite_once(tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    import sqlite3

    db = tmp_path / "tasker.sqlite"
    conn = sqlite3.connect(str(db))
    conn.execute(
        """
        CREATE TABLE items (
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
    conn.execute(
        "INSERT INTO items VALUES (?,?,?,?,?,?,?,?)",
        ("id-1", "旧任务", "urgent", "pin", '[{"stamp":"260915.3PM","text":"hello"}]', 1.0, 2.0, "urgent"),
    )
    conn.commit()
    conn.close()
    store = Store(tmp_path)
    loaded = store.get("id-1")
    assert loaded is not None
    assert loaded.title == "旧任务"
    assert loaded.state == "urgent"
    assert loaded.body_md == "260915.3PM\n\nhello"
    text = (tmp_path / "tasks" / "id-1.md").read_text(encoding="utf-8")
    assert "260915.3PM" in text
    assert "hello" in text

