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
