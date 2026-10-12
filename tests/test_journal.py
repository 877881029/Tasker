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


def test_line_separators_from_paste_become_newlines():
    from tasker.journal import dump_journal, normalize_breaks, parse_journal

    raw = "a\u2028\u2028b\r\nc\rd\u2029e\x0bf"
    assert normalize_breaks(raw) == "a\n\nb\nc\nd\ne\nf"
    body = "261012.4PM\n\n第一段\u2028\u2028第二段"
    entries = parse_journal(body)
    assert entries == [("261012.4PM", "第一段\n\n第二段")]
    assert "\u2028" not in dump_journal(entries)


def test_read_markup_breaks_on_line_separator():
    from tasker.shell.journal_edit import journal_log_markup

    html = journal_log_markup([("261012.4PM", "第一段\u2028\u2028第二段")])
    assert "第一段<br>&nbsp;<br>第二段" in html


def test_editor_paste_and_collect_normalize_separators(qtbot):
    from PySide6.QtCore import QMimeData
    from tasker.shell.journal_edit import JournalEditor

    editor = JournalEditor()
    qtbot.addWidget(editor)
    editor.load_entries([("261012.4PM", "")])
    mime = QMimeData()
    mime.setText("一\u2028\u2028二")
    editor.insertFromMimeData(mime)
    assert editor.entries() == [("261012.4PM", "一\n\n二")]
    assert editor.document().blockCount() == 3


def test_store_save_cleans_existing_separators(tmp_path):
    from dataclasses import replace
    from tasker.store import Store

    store = Store(tmp_path)
    item = store.save(replace(store.create(), body_md="261012.4PM\n\nx\u2028\u2028y"))
    assert "\u2028" not in (tmp_path / "tasks" / f"{item.id}.md").read_text(encoding="utf-8")
    assert store.get(item.id).body_md.endswith("x\n\ny")
