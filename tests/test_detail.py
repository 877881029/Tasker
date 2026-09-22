from datetime import datetime
from dataclasses import replace

from PySide6.QtCore import QMimeData, QRect, Qt
from PySide6.QtGui import QImage, QPalette

from PySide6.QtWidgets import QPlainTextEdit
from tasker.preview.md_edit import MarkdownEdit
from tasker.preview.md_visual import render_markdown
from tasker.shell.detail import DetailWindow, detail_geometry
from tasker.shell.journal_edit import journal_document_html
from tasker.store import Store
from tasker.theme import wrap_document_html, INK


def test_detail_geometry_fills_left():
    avail = QRect(0, 0, 1200, 800)
    geo = detail_geometry(avail, 400)
    assert geo.x() == 0
    assert geo.width() == 800


def test_render_markdown_escapes_raw_html_and_links():
    html = render_markdown('see <script>x</script> [hi](https://example.com)')
    assert "<script>" not in html
    assert "https://example.com" in html
    assert wrap_document_html("<p>x</p>").startswith("<!DOCTYPE html>")


def test_journal_document_html_keeps_one_stamp_column():
    html = journal_document_html(
        [
            ("260917.11AM", "已经合并了很长的一行文字需要折行到第二行"),
            ("260916.2PM", "短记录"),
        ]
    )
    assert "grid-template-columns" in html
    assert html.count("class='log'") + html.count('class="log"') == 1
    assert html.count("class='stamp") + html.count('class="stamp') == 2
    assert "Candara" in html
    assert "16px" in html
    assert "1.72" in html
    assert html.index("260917.11AM") < html.index("260916.2PM")


def test_journal_document_html_write_mode_is_contenteditable():
    html = journal_document_html(
        [("260918.10AM", "")],
        writable=True,
    )
    assert "contenteditable" in html
    assert "16px" in html
    assert "Candara" in html
    assert "_journalDirty" in html
    assert "preventDefault" in html
    html_ro = journal_document_html([("260918.10AM", "正文")])
    assert 'contenteditable="true"' not in html_ro
    assert "_journalDirty" not in html_ro


def test_journal_document_view_uses_chromium():
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from tasker.shell.journal_edit import JournalDocumentView

    assert issubclass(JournalDocumentView, QWebEngineView)


def test_paste_image_writes_attachment(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path)
    item = store.create()
    edit = MarkdownEdit(store, item.id)
    qtbot.addWidget(edit)
    image = QImage(4, 4, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.blue)
    mime = QMimeData()
    mime.setImageData(image)
    edit.insertFromMimeData(mime)
    text = edit.toPlainText()
    assert text.startswith("![](")
    assert (tmp_path / "tasks" / item.id).exists()
    assert list((tmp_path / "tasks" / item.id).glob("*.png"))


def _insert_head(win, text: str) -> None:
    cursor = win.journal.head_edit().textCursor()
    cursor.insertText(text)
    win.journal.head_edit().setTextCursor(cursor)


def test_open_is_readonly_until_ctrl_i(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path)
    item = store.save(replace(store.create(), body_md="260915.3PM\n\n旧记录"))
    win = DetailWindow(store)
    qtbot.addWidget(win)
    win.load(item)
    editors = win.journal.findChildren(QPlainTextEdit)
    assert len(editors) == 1
    assert win.journal.head_edit().isReadOnly()
    win.begin_write()
    assert not win.journal.head_edit().isReadOnly()
    assert win.journal.head_edit().entries()[1][1] == "旧记录"


def test_ctrl_i_same_hour_two_records(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path)
    item = store.create()
    win = DetailWindow(store)
    qtbot.addWidget(win)
    win.load(item)
    when = datetime(2026, 9, 15, 15, 1)
    win.journal.begin_write(when)
    _insert_head(win, "第一条")
    win.journal.begin_write(when)
    _insert_head(win, "第二条")
    assert [stamp for stamp, _text in win.journal.head_edit().entries()] == [
        "260915.3PM",
        "260915.3PM",
    ]
    blob = win.journal.collect()
    assert blob == "260915.3PM\n\n第二条\n\n260915.3PM\n\n第一条"


def test_ctrl_i_without_text_drops_empty_stamp(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path)
    item = store.save(replace(store.create(), body_md="260915.3PM\n\n旧记录"))
    win = DetailWindow(store)
    qtbot.addWidget(win)
    win.load(item)
    win.journal.begin_write(datetime(2026, 9, 17, 14, 0))
    win.save_keep_open()
    blob = win.journal.collect()
    assert "260917.2PM" not in blob
    assert win.journal.head_edit().entries() == [("260915.3PM", "旧记录")]
    loaded = store.get(item.id)
    assert loaded is not None
    assert "260917.2PM" not in loaded.body_md


def test_ctrl_i_can_edit_older_record(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path)
    item = store.save(replace(store.create(), body_md="260915.3PM\n\n旧记录"))
    win = DetailWindow(store)
    qtbot.addWidget(win)
    win.load(item)
    when = datetime(2026, 9, 15, 16, 0)
    win.journal.begin_write(when)
    _insert_head(win, "新记录")
    older = None
    block = win.journal.head_edit().document().begin()
    while block.isValid():
        if block.text() == "旧记录":
            older = block
            break
        block = block.next()
    assert older is not None
    cursor = win.journal.head_edit().textCursor()
    cursor.setPosition(older.position())
    cursor.movePosition(cursor.MoveOperation.EndOfBlock)
    cursor.insertText("已改")
    blob = win.journal.collect()
    assert "新记录" in blob
    assert "旧记录已改" in blob


def test_journal_gap_is_one_blank_line(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path)
    item = store.save(
        replace(
            store.create(),
            body_md="260916.11AM\n\n上一条短记录\n\n260916.10AM\n\n下一条短记录",
        )
    )
    win = DetailWindow(store)
    qtbot.addWidget(win)
    win.resize(720, 640)
    win.show()
    win.load(item)
    qtbot.wait(30)
    rows: list[tuple[str, str]] = []
    block = win.journal.head_edit().document().begin()
    while block.isValid():
        data = block.userData()
        stamp = getattr(data, "stamp", "") if data is not None else ""
        rows.append((stamp, block.text()))
        block = block.next()
    assert rows == [
        ("260916.11AM", "上一条短记录"),
        ("", ""),
        ("260916.10AM", "下一条短记录"),
    ]


def test_journal_uses_reader_document_font(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path)
    win = DetailWindow(store)
    qtbot.addWidget(win)
    win.load(store.create())
    win.begin_write()
    edit = win.journal.head_edit()
    assert "Candara" in edit.font().families() or edit.font().family()
    assert edit.font().pixelSize() == 16
    assert win.journal.stack.currentWidget() is edit


def test_readonly_journal_uses_reader_document_css(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path)
    item = store.save(replace(store.create(), body_md="260915.3PM\n\n旧记录"))
    win = DetailWindow(store)
    qtbot.addWidget(win)
    win.load(item)
    html = win.journal.document_html()
    assert "Candara" in html
    assert "1.72" in html
    assert "16px" in html
    assert INK.lstrip("#") in html.lower() or INK in html
    assert win.journal.stack.currentWidget() is win.journal.document_view
    win.begin_write()
    assert win.journal.stack.currentWidget() is win.journal.head_edit()
    assert not win.journal.head_edit().isReadOnly()


def test_journal_readonly_body_uses_ink(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path)
    item = store.save(replace(store.create(), body_md="260915.3PM\n\n旧记录"))
    win = DetailWindow(store)
    qtbot.addWidget(win)
    win.load(item)
    edit = win.journal.head_edit()
    assert edit.isReadOnly()
    pal = edit.palette()
    for group in (
        QPalette.ColorGroup.Active,
        QPalette.ColorGroup.Inactive,
        QPalette.ColorGroup.Disabled,
    ):
        assert pal.color(group, QPalette.ColorRole.Text).name() == INK
        assert edit.viewport().palette().color(group, QPalette.ColorRole.Text).name() == INK


def test_journal_is_one_scrolling_editor(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path)
    body = (
        "260916.11AM\n\n"
        "这份文档有一个小优化应该是, 我们应该重点强调一下, 之前已经有了的skill不会在最新的部署脚本中覆盖"
        " 同时如果不是最新脚本来部署的, 那么其使用时也就不会被dashboard中检测到"
    )
    item = store.save(replace(store.create(), body_md=body))
    win = DetailWindow(store)
    qtbot.addWidget(win)
    win.resize(640, 480)
    win.show()
    win.load(item)
    qtbot.wait(80)
    edit = win.journal.head_edit()
    assert len(win.journal.findChildren(QPlainTextEdit)) == 1
    assert edit.gutter().width() == 118
    visible = win.journal.stack.currentWidget()
    assert visible is win.journal.document_view
    assert visible.height() == win.journal.height()
    assert edit.maximumHeight() > 10000


def test_ctrl_s_keeps_chromium_text_when_dirty_flag_missing(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path)
    item = store.save(replace(store.create(), body_md="260915.3PM\n\n旧记录"))
    win = DetailWindow(store)
    qtbot.addWidget(win)
    win.load(item)
    win.begin_write()
    _insert_head(win, "刚写在详情里的内容")
    win.save_keep_open()
    loaded = store.get(item.id)
    assert loaded is not None
    assert "刚写在详情里的内容" in loaded.body_md
    assert "旧记录" in loaded.body_md
    assert win.journal.stack.currentWidget() is win.journal.document_view
    assert 'contenteditable="true"' not in win.journal.document_html()


def test_ctrl_s_does_not_wipe_when_chromium_returns_blank_texts(
    qtbot, tmp_path, monkeypatch
):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path)
    item = store.save(replace(store.create(), body_md="260915.3PM\n\n旧记录"))
    win = DetailWindow(store)
    qtbot.addWidget(win)
    win.load(item)
    win.begin_write()
    win.journal.document_view.read_write_state = lambda: (
        True,
        [("260918.10AM", ""), ("260915.3PM", "")],
    )
    win.save_keep_open()
    loaded = store.get(item.id)
    assert loaded is not None
    assert "旧记录" in loaded.body_md
    assert win.journal.head_edit().entries()
    html = win.journal.document_html()
    assert "旧记录" in html


def test_ctrl_s_keeps_old_text_when_pull_blanks_older_row(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path)
    item = store.save(replace(store.create(), body_md="260915.3PM\n\n旧记录"))
    win = DetailWindow(store)
    qtbot.addWidget(win)
    win.load(item)
    win.begin_write()
    _insert_head(win, "新写的一行")
    win.save_keep_open()
    loaded = store.get(item.id)
    assert loaded is not None
    assert "新写的一行" in loaded.body_md
    assert "旧记录" in loaded.body_md


def test_ctrl_s_keeps_editor_when_chromium_returns_no_rows(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path)
    item = store.create()
    win = DetailWindow(store)
    qtbot.addWidget(win)
    win.load(item)
    win.begin_write()
    _insert_head(win, "已接到 setup")
    win.journal.document_view.read_write_state = lambda: (False, [])
    win.save_keep_open()
    loaded = store.get(item.id)
    assert loaded is not None
    assert "已接到 setup" in loaded.body_md


def test_ctrl_s_writes_and_stays_readonly(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path)
    item = store.create()
    win = DetailWindow(store)
    qtbot.addWidget(win)
    win.show()
    win.load(item)
    win.begin_write()
    _insert_head(win, "已接到 setup")
    win.journal.document_view.read_write_state = lambda: None
    win.title_edit.setText("改脚本")
    win.save_keep_open()
    loaded = store.get(item.id)
    assert loaded is not None
    assert loaded.status_pin == "已接到 setup"
    assert loaded.title == "改脚本"
    assert win.journal.head_edit().isReadOnly()
    assert win.isVisible()
    assert getattr(win, "save_btn", None) is None
    assert getattr(win, "close_btn", None) is None


def test_journal_status_tracks_read_write_and_saved_modes(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path)
    first = store.create()
    second = store.create()
    win = DetailWindow(store)
    qtbot.addWidget(win)

    win.load(first)
    assert win.journal_status.text() == "Ctrl+I 写入 · Ctrl+S 保存 · Esc 收起"
    assert win.journal_status.focusPolicy() == Qt.FocusPolicy.NoFocus

    win.begin_write()
    assert win.journal_status.text() == "正在写入 · Ctrl+S 保存 · Esc 保存并收起"

    _insert_head(win, "状态反馈")
    win.save_keep_open()
    assert win.journal_status.text() == "已保存 · Ctrl+I 继续写入 · Esc 收起"

    win.load(second)
    assert win.journal_status.text() == "Ctrl+I 写入 · Ctrl+S 保存 · Esc 收起"


def test_detail_controls_expose_accessible_names(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path)
    item = store.create()
    win = DetailWindow(store)
    qtbot.addWidget(win)
    win.load(item)

    assert win.title_edit.accessibleName() == "任务标题"
    assert win.done.accessibleName() == "完成任务"
    assert "任务状态" in win.importance.accessibleName()
    assert win.delete_btn.accessibleName() == "删除任务"
    assert win.journal.head_edit().accessibleName() == "任务日志编辑器"
    assert win.journal.document_view.accessibleName() == "任务日志只读内容"


def test_ctrl_s_keeps_text_typed_in_write_editor(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path)
    item = store.create()
    win = DetailWindow(store)
    qtbot.addWidget(win)
    win.load(item)
    win.begin_write()
    assert win.journal.stack.currentWidget() is win.journal.head_edit()
    _insert_head(win, "开始测试")
    win.save_keep_open()
    loaded = store.get(item.id)
    assert loaded is not None
    assert "开始测试" in loaded.body_md
    assert win.journal.stack.currentWidget() is win.journal.document_view
    assert 'contenteditable="true"' not in win.journal.document_html()


def test_image_absolute_path_unchanged_on_save(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path)
    path = "C:/Users/me/Pictures/shot.png"
    item = store.save(replace(store.create(), body_md=f"260915.3PM\n\n![]({path})"))
    win = DetailWindow(store)
    qtbot.addWidget(win)
    win.load(item)
    win.save_keep_open()
    loaded = store.get(item.id)
    assert loaded is not None
    assert path in loaded.body_md


def test_detail_cycle_and_delete(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path)
    item = store.create()
    win = DetailWindow(store)
    qtbot.addWidget(win)
    win.load(item)
    win.importance.click()
    loaded = store.get(item.id)
    assert loaded is not None and loaded.state == "urgent"
    win.delete_btn.click()
    assert store.get(item.id) is not None
    assert win.delete_btn.text() == "确认删除"
    win.delete_btn.click()
    assert store.get(item.id) is None
    assert not (tmp_path / "tasks" / f"{item.id}.md").exists()
    assert not win.isVisible()


def test_delete_confirmation_resets_on_load_and_timeout(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(DetailWindow, "DELETE_CONFIRM_MS", 10)
    store = Store(tmp_path)
    first = store.create()
    second = store.create()
    win = DetailWindow(store)
    qtbot.addWidget(win)

    win.load(first)
    win.delete_btn.click()
    assert win.delete_btn.text() == "确认删除"
    win.load(second)
    assert win.delete_btn.text() == "删除"
    assert store.get(first.id) is not None

    win.delete_btn.click()
    qtbot.waitUntil(lambda: win.delete_btn.text() == "删除", timeout=500)
    assert store.get(second.id) is not None
