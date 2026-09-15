from datetime import datetime

from tasker.journal import dump_journal, parse_journal, prepend_record, stamp_for


def test_stamp_is_yymmdd_hour_ampm():
    when = datetime(2026, 9, 15, 15, 12)
    assert stamp_for(when) == "260915.3PM"
    assert stamp_for(datetime(2026, 9, 15, 0, 5)) == "260915.12AM"


def test_dump_separates_records_with_one_blank_line():
    blob = dump_journal([("260915.4PM", "新"), ("260915.3PM", "旧")])
    assert blob == "260915.4PM\n\n新\n\n260915.3PM\n\n旧"
    assert parse_journal(blob) == [("260915.4PM", "新"), ("260915.3PM", "旧")]


def test_prepend_record_same_hour_is_new_entry():
    when = datetime(2026, 9, 15, 15, 1)
    once = prepend_record([("260915.3PM", "已有")], when)
    twice = prepend_record(once, when)
    assert [e[0] for e in twice] == ["260915.3PM", "260915.3PM", "260915.3PM"]
    assert dump_journal(twice).count("260915.3PM") == 3


def test_parse_dump_roundtrip_and_legacy_markdown():
    entries = [("260915.3PM", "最新"), ("260915.2PM", "更早")]
    blob = dump_journal(entries)
    assert parse_journal(blob) == entries
    assert parse_journal("") == []
    assert parse_journal("# 旧正文") == [("", "# 旧正文")]
    assert parse_journal('[{"stamp":"260915.3PM","text":"json旧"}]') == [
        ("260915.3PM", "json旧")
    ]
