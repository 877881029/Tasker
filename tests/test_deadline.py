import re
import time
from dataclasses import replace
from datetime import datetime, timedelta

from PySide6.QtCore import QDateTime

from tasker.deadline import countdown_text, deadline_presets, format_countdown
from tasker.store import Store


def _store(tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    return Store(tmp_path)


def test_format_countdown_pads_days_hours_minutes():
    assert format_countdown(timedelta(days=3, hours=14, minutes=57, seconds=40)) == "03d-14h-57m"
    assert format_countdown(timedelta(minutes=5)) == "00d-00h-05m"
    assert format_countdown(timedelta(days=120)) == "120d-00h-00m"
    assert format_countdown(timedelta(0)) == "00d-00h-00m"


def test_countdown_text_marks_soon_and_overdue():
    now = datetime(2026, 10, 12, 10, 0)
    assert countdown_text(datetime(2026, 10, 15, 23, 0), now) == ("03d-13h-00m", "normal")
    assert countdown_text(datetime(2026, 10, 12, 20, 30), now) == ("00d-10h-30m", "soon")
    assert countdown_text(datetime(2026, 10, 11, 8, 57), now) == ("超期 01d-01h-03m", "overdue")


def test_deadline_presets_are_future_and_ordered():
    now = datetime(2026, 10, 12, 19, 0)  # Monday evening, past 18:00
    presets = dict(deadline_presets(now))
    assert presets["明天 18:00"] == datetime(2026, 10, 13, 18, 0)
    assert presets["3 天后 18:00"] == datetime(2026, 10, 15, 18, 0)
    assert presets["下周一 09:00"] == datetime(2026, 10, 19, 9, 0)
    assert "今天 18:00" not in presets
    morning = dict(deadline_presets(datetime(2026, 10, 12, 9, 0)))
    assert morning["今天 18:00"] == datetime(2026, 10, 12, 18, 0)


def test_deadline_round_trips_and_old_files_have_none(tmp_path, monkeypatch):
    store = _store(tmp_path, monkeypatch)
    item = store.save(replace(store.create(), title="交付"))
    assert item.deadline is None
    assert "deadline" not in (tmp_path / "tasks" / f"{item.id}.md").read_text(encoding="utf-8")
    when = datetime(2026, 10, 15, 18, 0)
    saved = store.set_deadline(item.id, when)
    assert saved.deadline == when
    text = (tmp_path / "tasks" / f"{item.id}.md").read_text(encoding="utf-8")
    assert "2026-10-15T18:00" in text
    assert store.get(item.id).deadline == when
    assert store.set_deadline(item.id, None).deadline is None
    assert store.get(item.id).deadline is None


def test_deadline_survives_state_changes(tmp_path, monkeypatch):
    store = _store(tmp_path, monkeypatch)
    item = store.cycle_color(store.create().id)
    store.set_deadline(item.id, datetime(2026, 10, 15, 18, 0))
    store.cycle_color(item.id)
    store.set_done(item.id, True)
    back = store.set_done(item.id, False)
    assert back.deadline == datetime(2026, 10, 15, 18, 0)


def test_urgent_sorted_by_deadline_then_recent(tmp_path, monkeypatch):
    store = _store(tmp_path, monkeypatch)

    def urgent(title, when=None):
        time.sleep(0.02)
        item = store.cycle_color(store.save(replace(store.create(), title=title)).id)
        if when is not None:
            item = store.set_deadline(item.id, when)
        return item

    urgent("无DDL旧")
    urgent("远", datetime(2026, 11, 1, 9, 0))
    store.save(replace(store.create(), title="普通"))
    urgent("近", datetime(2026, 10, 13, 9, 0))
    urgent("无DDL新")
    pending_with_ddl = store.save(replace(store.create(), title="普通带DDL"))
    store.set_deadline(pending_with_ddl.id, datetime(2026, 10, 12, 9, 0))
    titles = [item.title for item in store.list_visible()]
    assert titles[:4] == ["近", "远", "无DDL新", "无DDL旧"]
    assert set(titles[4:]) == {"普通", "普通带DDL"}


def test_qdatetime_helpers_round_trip():
    from tasker.deadline import from_qdatetime, to_qdatetime

    when = datetime(2026, 10, 15, 18, 0)
    assert from_qdatetime(to_qdatetime(when)) == when
    assert isinstance(to_qdatetime(when), QDateTime)


def _ui_dock(qtbot, tmp_path, monkeypatch):
    from dataclasses import replace as _replace

    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    from tasker.shell.window import DockWindow

    store = Store(tmp_path / "tasker.sqlite")
    a = store.save(_replace(store.create(), title="甲", state="urgent"))
    b = store.save(_replace(store.create(), title="乙", state="urgent"))
    c = store.save(_replace(store.create(), title="丙"))
    dock = DockWindow(store)
    qtbot.addWidget(dock)
    dock.show()
    return dock, store, a, b, c


def test_list_pill_shows_countdown_for_urgent_with_deadline(qtbot, tmp_path, monkeypatch):
    dock, store, a, _b, c = _ui_dock(qtbot, tmp_path, monkeypatch)
    soon = datetime.now().replace(second=0, microsecond=0) + timedelta(days=3, hours=2)
    store.set_deadline(a.id, soon)
    store.set_deadline(c.id, soon)
    dock.refresh()
    cards = {card.item_id: card for card in dock.cards()}
    pill = cards[a.id].deadline_pill
    assert not pill.isHidden()
    assert re.fullmatch(r"\d{2}d-\d{2}h-\d{2}m", pill.text())
    assert cards[c.id].deadline_pill.isHidden()
    assert dock.cards()[0].item_id == a.id


def test_list_pill_overdue_tone(qtbot, tmp_path, monkeypatch):
    dock, store, a, _b, _c = _ui_dock(qtbot, tmp_path, monkeypatch)
    store.set_deadline(a.id, datetime.now() - timedelta(hours=2))
    dock.refresh()
    card = next(card for card in dock.cards() if card.item_id == a.id)
    assert card.deadline_pill.text().startswith("超期 ")
    assert card.deadline_pill.property("tone") == "overdue"


def test_detail_pick_deadline_saves_and_resorts(qtbot, tmp_path, monkeypatch):
    dock, store, a, b, _c = _ui_dock(qtbot, tmp_path, monkeypatch)
    store.set_deadline(a.id, datetime.now() + timedelta(days=5))
    dock.refresh()
    dock.open_detail(b.id)
    detail = dock._detail
    assert detail.deadline_btn.isVisibleTo(detail)
    assert detail.deadline_btn.text().startswith("设置 DDL")
    target = datetime.now().replace(second=0, microsecond=0) + timedelta(days=1)
    detail.set_deadline(target)
    assert store.get(b.id).deadline == target
    assert detail.deadline_btn.text().startswith("DDL ")
    assert dock.cards()[0].item_id == b.id
    detail.set_status("pending")
    assert not detail.deadline_btn.isVisibleTo(detail)
    assert store.get(b.id).deadline == target


def test_detail_menu_has_presets_and_clear(qtbot, tmp_path, monkeypatch):
    dock, store, a, _b, _c = _ui_dock(qtbot, tmp_path, monkeypatch)
    dock.open_detail(a.id)
    menu = dock._detail.deadline_btn.menu()
    texts = [action.text() for action in menu.actions() if action.text()]
    assert "清除 DDL" in texts
    assert any("明天" in text for text in texts)
    assert menu.deadline_edit is not None
