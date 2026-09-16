from datetime import datetime
from dataclasses import replace

from PySide6.QtCore import QMimeData, QRect, Qt
from PySide6.QtGui import QImage

from PySide6.QtWidgets import QPlainTextEdit
from tasker.preview.md_edit import MarkdownEdit
from tasker.preview.md_visual import render_markdown
from tasker.shell.detail import DetailWindow, detail_geometry
from tasker.store import Store
from tasker.theme import wrap_document_html


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


def test_open_is_readonly_until_ctrl_i(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path)
    item = store.save(replace(store.create(), body_md="260915.3PM\n\n旧记录"))
    win = DetailWindow(store)
    qtbot.addWidget(win)
    win.load(item)
    assert win.journal._rows
    assert win.journal.head_edit().isReadOnly()
    win.begin_write()
    assert not win.journal.head_edit().isReadOnly()
    assert len(win.journal._rows) == 2


def test_ctrl_i_same_hour_two_records(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path)
    item = store.create()
    win = DetailWindow(store)
    qtbot.addWidget(win)
    win.load(item)
    when = datetime(2026, 9, 15, 15, 1)
    win.journal.begin_write(when)
    win.journal.head_edit().setPlainText("第一条")
    win.journal.begin_write(when)
    win.journal.head_edit().setPlainText("第二条")
    assert [row[0].text() for row in win.journal._rows] == ["260915.3PM", "260915.3PM"]
    blob = win.journal.collect()
    assert blob == "260915.3PM\n\n第二条\n\n260915.3PM\n\n第一条"


def test_journal_gap_is_about_two_line_heights(qtbot, tmp_path, monkeypatch):
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
    first = win.journal._list.itemAt(0).widget()
    second = win.journal._list.itemAt(1).widget()
    edit = first.findChild(QPlainTextEdit)
    line = edit.fontMetrics().lineSpacing()
    gap = second.y() - (first.y() + first.height())
    assert first.height() <= line * 5
    assert 0 < gap <= line * 3


def test_ctrl_s_writes_and_stays_readonly(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path)
    item = store.create()
    win = DetailWindow(store)
    qtbot.addWidget(win)
    win.show()
    win.load(item)
    win.begin_write()
    win.journal.head_edit().setPlainText("已接到 setup")
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
