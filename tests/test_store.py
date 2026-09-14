from dataclasses import replace

from tasker.store import Store


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


def test_write_paste_png(tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path / "tasker.sqlite")
    item = store.create()
    path = store.write_paste_png(item.id, b"\x89PNG")
    assert path.exists()
    assert path.parent.name == item.id
    assert path.read_bytes().startswith(b"\x89PNG")
