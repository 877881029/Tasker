import uuid
from dataclasses import replace
from datetime import datetime, timedelta

from tasker.reminders import ReminderTracker, badge_text, overdue_count
from tasker.report import stamp_date, summary_line, week_bounds, weekly_report
from tasker.shell.autostart import is_enabled, set_enabled
from tasker.shell.quick_capture import parse_capture
from tasker.store import Item, Store

NOW = datetime(2026, 10, 14, 10, 0)


def _item(**kw) -> Item:
    base = Item(
        id=str(uuid.uuid4()),
        title="t",
        state="urgent",
        status_pin="",
        body_md="",
        created_at=0.0,
        updated_at=0.0,
        resume_state="urgent",
    )
    return replace(base, **kw)


# ---- search keywords -------------------------------------------------------

def test_search_keywords_union_with_text(tmp_path):
    store = Store(tmp_path)
    urgent = store.save(replace(store.create(), title="甲", state="urgent", resume_state="urgent"))
    late = store.save(replace(store.create(), title="乙", state="urgent", resume_state="urgent"))
    store.set_deadline(late.id, datetime.now() - timedelta(hours=1))
    done = store.save(replace(store.create(), title="丙", state="done"))
    plain = store.save(replace(store.create(), title="写紧急预案"))
    ids = lambda q: {item.id for item in store.list_visible(q)}
    assert ids("紧急") == {urgent.id, late.id, plain.id}
    assert ids("超期") == {late.id}
    assert ids("DDL") == {late.id}
    assert ids("已完成") == {done.id}
    assert ids("普通") == {plain.id}
    today = store.set_deadline(urgent.id, datetime.now().replace(hour=23, minute=59))
    assert today.id in ids("今天")


def test_search_matches_journal_body(tmp_path):
    store = Store(tmp_path)
    item = store.save(replace(store.create(), title="x", body_md="261012.3PM\n\n注册表位置"))
    assert [i.id for i in store.list_visible("注册表")] == [item.id]


def test_raw_snapshot_restore_round_trip(tmp_path):
    store = Store(tmp_path)
    item = store.save(replace(store.create(), title="留", body_md="261012.3PM\n\n内容"))
    raw = store.read_raw(item.id)
    store.delete(item.id)
    assert store.get(item.id) is None
    back = store.restore_raw(item.id, raw)
    assert back.title == "留" and "内容" in back.body_md
    assert store.read_raw("missing") is None


# ---- reminders -------------------------------------------------------------

def test_overdue_count_and_badge():
    items = [
        _item(deadline=NOW - timedelta(minutes=1)),
        _item(deadline=NOW + timedelta(hours=2)),
        _item(state="pending", deadline=NOW - timedelta(days=1)),
    ]
    assert overdue_count(items, NOW) == 1
    assert badge_text(0) == "" and badge_text(3) == "3" and badge_text(12) == "9+"


def test_startup_summarizes_overdue_then_notifies_individually():
    tracker = ReminderTracker()
    late = _item(title="旧", deadline=NOW - timedelta(hours=3))
    soon = _item(title="快", deadline=NOW + timedelta(minutes=40))
    later = _item(title="后", deadline=NOW + timedelta(minutes=90))
    first = tracker.check([late, soon, later], NOW)
    assert [r.kind for r in first] == ["summary", "soon"]
    assert "1 个任务已超期" in first[0].body
    assert first[1].item_id == soon.id and "快" in first[1].body
    assert tracker.check([late, soon, later], NOW) == []
    step = NOW + timedelta(minutes=35)
    assert [(r.kind, r.item_id) for r in tracker.check([late, soon, later], step)] == [
        ("soon", later.id)
    ]
    step = NOW + timedelta(minutes=41)
    out = tracker.check([late, soon, later], step)
    assert [(r.kind, r.item_id) for r in out] == [("overdue", soon.id)]


def test_changing_deadline_rearms_reminder():
    tracker = ReminderTracker()
    item = _item(deadline=NOW + timedelta(minutes=30))
    assert len(tracker.check([item], NOW)) == 1
    moved = replace(item, deadline=NOW + timedelta(minutes=50))
    assert [r.kind for r in tracker.check([moved], NOW)] == ["soon"]


def test_missed_soon_window_only_sends_overdue():
    tracker = ReminderTracker()
    tracker.check([], NOW)
    item = _item(deadline=NOW - timedelta(minutes=1))
    assert [r.kind for r in tracker.check([item], NOW)] == ["overdue"]


# ---- report ----------------------------------------------------------------

def test_stamp_date_and_week_bounds():
    assert stamp_date("261012.3PM") == datetime(2026, 10, 12).date()
    assert stamp_date("bad") is None
    start, end = week_bounds(NOW)
    assert (start.isoformat(), end.isoformat()) == ("2026-10-12", "2026-10-18")


def test_weekly_report_groups_and_filters_by_week():
    body = "261014.9AM\n\n第一行\n续行\n\n261013.3PM\n\n昨天\n\n261009.3PM\n\n上周"
    items = [
        _item(title="紧", deadline=datetime(2026, 10, 16, 18, 0), body_md=body),
        _item(title="普", state="pending", body_md="261012.10AM\n\n![x](a.png)"),
        _item(title="完", state="done", body_md="261001.1PM\n\n很早"),
    ]
    text, count = weekly_report(items, NOW)
    assert count == 2
    assert text.startswith("# 周报 2026-10-12 ~ 2026-10-18")
    assert "## 紧急\n### 紧（DDL 10-16 18:00）\n- 10-14 9AM：第一行\n  续行\n- 10-13 3PM：昨天" in text
    assert "上周" not in text and "## 已完成" not in text
    assert "- 10-12 10AM：[图片]" in text


def test_weekly_report_empty():
    text, count = weekly_report([], NOW)
    assert count == 0 and "本周暂无记录" in text


def test_summary_line():
    assert summary_line("") == ""
    assert summary_line("\n  第一行\n第二行") == "第一行"
    assert summary_line("![p](x.png) 看图") == "[图片] 看图"


# ---- quick capture / autostart --------------------------------------------

def test_parse_capture():
    assert parse_capture("  买咖啡 ") == ("买咖啡", False)
    assert parse_capture("!修 bug") == ("修 bug", True)
    assert parse_capture("！ 交周报") == ("交周报", True)
    assert parse_capture("   ") == ("", False)


def test_autostart_round_trip():
    key = r"Software\TaskerTestRun" + uuid.uuid4().hex[:6]
    try:
        assert not is_enabled(key)
        assert set_enabled(True, '"C:\\x\\Tasker.exe"', key=key)
        assert is_enabled(key)
        assert set_enabled(False, key=key)
        assert not is_enabled(key)
    finally:
        import winreg

        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key)
        except OSError:
            pass
