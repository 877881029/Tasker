from datetime import datetime

from tasker.journal import dump_journal, ensure_current, parse_journal, stamp_for


def test_stamp_is_yymmdd_hour_ampm():
    when = datetime(2026, 9, 15, 15, 12)
    assert stamp_for(when) == "260915.3PM"
    assert stamp_for(datetime(2026, 9, 15, 0, 5)) == "260915.12AM"


def test_ensure_current_prepends_new_hour():
    older = [("260915.2PM", "旧记录")]
    now = datetime(2026, 9, 15, 15, 1)
    out = ensure_current(older, now)
    assert out[0] == ("260915.3PM", "")
    assert out[1][1] == "旧记录"
    assert ensure_current(out, now)[0][0] == "260915.3PM"


def test_parse_dump_roundtrip_and_legacy_markdown():
    entries = [("260915.3PM", "最新"), ("260915.2PM", "更早")]
    blob = dump_journal(entries)
    assert parse_journal(blob) == entries
    assert parse_journal("") == []
    assert parse_journal("# 旧正文") == [("", "# 旧正文")]
