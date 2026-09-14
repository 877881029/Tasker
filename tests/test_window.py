from PySide6.QtCore import QRect

from tasker.shell.window import geometry_for_screen
from tasker.store import Store
from tasker.theme import DONE_BG


def test_geometry_is_right_third():
    avail = QRect(0, 0, 1200, 800)
    geo = geometry_for_screen(avail)
    assert geo.width() == 400
    assert geo.x() == 800
    assert geo.height() == 800


def test_add_search_done_and_color(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    from tasker.shell.window import DockWindow

    store = Store(tmp_path / "tasker.sqlite")
    dock = DockWindow(store)
    qtbot.addWidget(dock)
    dock.add_btn.click()
    assert dock._detail is None or not dock._detail.isVisible()
    assert len(store.list_visible()) == 1
    card = dock.list_layout.itemAt(0).widget()
    card.title.setText("PDF 默认应用")
    card.title.editingFinished.emit()
    card._save_title()
    dock.add_btn.click()
    other = dock.list_layout.itemAt(0).widget()
    # list re-rendered; find PDF
    dock.search.setText("PDF")
    assert dock.list_layout.count() == 1
    only = dock.list_layout.itemAt(0).widget()
    assert "PDF" in only.title.text()
    only.color_bar.click()
    item = store.get(only.item_id)
    assert item is not None and item.state == "urgent"
    only.done.setChecked(True)
    item = store.get(only.item_id)
    assert item is not None and item.state == "done"
    assert DONE_BG in only.styleSheet()
    assert "line-through" not in only.styleSheet()


def test_pin_sets_stays_on_top(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    from PySide6.QtCore import Qt
    from tasker.shell.window import DockWindow

    dock = DockWindow(Store(tmp_path / "tasker.sqlite"))
    qtbot.addWidget(dock)
    dock.pin_btn.setChecked(True)
    assert dock.windowFlags() & Qt.WindowType.WindowStaysOnTopHint
    dock.pin_btn.setChecked(False)
    assert not (dock.windowFlags() & Qt.WindowType.WindowStaysOnTopHint)


def test_detail_save_and_close(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    from tasker.shell.window import DockWindow

    store = Store(tmp_path / "tasker.sqlite")
    dock = DockWindow(store)
    qtbot.addWidget(dock)
    item = store.create()
    dock.open_detail(item.id)
    assert dock._detail is not None
    assert dock._detail.isVisible()
    assert dock._detail.close_btn.text() == "关闭"
    assert dock._detail.save_btn.text() == "保存"
    dock._detail.title_edit.setText("可关闭的任务")
    dock._detail.editor.setPlainText("正文")
    dock._detail.save_btn.click()
    loaded = store.get(item.id)
    assert loaded is not None
    assert loaded.title == "可关闭的任务"
    assert loaded.body_md == "正文"
    dock._detail.close_btn.click()
    assert not dock._detail.isVisible()

