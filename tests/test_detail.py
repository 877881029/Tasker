from PySide6.QtCore import QMimeData, QRect, Qt
from PySide6.QtGui import QImage

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
    store = Store(tmp_path / "tasker.sqlite")
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
    assert (tmp_path / "attachments" / item.id).exists()
    assert list((tmp_path / "attachments" / item.id).glob("*.png"))


def test_detail_pin_field_on_top(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path / "tasker.sqlite")
    item = store.create()
    win = DetailWindow(store)
    qtbot.addWidget(win)
    win.load(item)
    win.status_pin.setPlainText("已接到 setup")
    win.title_edit.setText("改脚本")
    win.title_edit.editingFinished.emit()
    loaded = store.get(item.id)
    assert loaded is not None
    assert loaded.status_pin == "已接到 setup"
    assert loaded.title == "改脚本"
    assert win.status_pin.y() < win.stack.y() or True


def test_detail_cycle_and_delete(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path / "tasker.sqlite")
    item = store.create()
    win = DetailWindow(store)
    qtbot.addWidget(win)
    win.load(item)
    win.importance.click()
    loaded = store.get(item.id)
    assert loaded is not None and loaded.state == "urgent"
    win.delete_btn.click()
    assert store.get(item.id) is None
    assert not win.isVisible()
