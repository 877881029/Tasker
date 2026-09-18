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
    family = edit.font().family()
    assert family in {"Candara", "Calibri", "Segoe UI"}
    assert edit.gutter_font().family() == family
    assert edit.font().pixelSize() == 16
    assert edit.gutter_font().pixelSize() == 13
    assert int(edit.gutter_font().weight()) == 600
    assert edit.autoFillBackground()
    assert edit.viewport().autoFillBackground()


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
    assert win.journal.stack.currentWidget() is win.journal.editor


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
    assert store.get(item.id) is None
    assert not (tmp_path / "tasks" / f"{item.id}.md").exists()
    assert not win.isVisible()
