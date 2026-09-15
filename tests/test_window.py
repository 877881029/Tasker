from dataclasses import replace

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtWidgets import QLabel, QSizePolicy, QToolButton

from tasker.shell.window import geometry_for_screen
from tasker.store import Store
from tasker.theme import DONE_BG, PAPER, dock_style


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
    assert dock._detail is not None and dock._detail.isVisible()
    assert len(store.list_visible()) == 1
    dock._detail.title_edit.setText("PDF 默认应用")
    dock._detail.save_keep_open()
    dock._detail.close_detail()
    dock.add_btn.click()
    dock._detail.close_detail()
    dock.search.setText("PDF")
    assert dock.list_layout.count() == 1
    only = dock.list_layout.itemAt(0).widget()
    assert "PDF" in only.title.text()
    before = store.get(only.item_id)
    assert before is not None
    qtbot.mouseClick(only, Qt.MouseButton.LeftButton)
    assert dock._detail.isVisible()
    assert store.get(only.item_id).state == before.state
    dock._detail.importance.click()
    item = store.get(only.item_id)
    assert item is not None and item.state == "urgent"
    assert getattr(only, "done", None) is None
    assert only.findChild(QToolButton, "openDetail") is None
    assert "border-radius:10px" in only.importance.styleSheet()
    assert only.title.minimumHeight() >= 72
    dock._detail.done.setChecked(True)
    item = store.get(only.item_id)
    assert item is not None and item.state == "done"
    dock._detail.close_detail()
    only = dock.list_layout.itemAt(0).widget()
    assert DONE_BG in only.styleSheet()
    assert "line-through" not in only.styleSheet()


def test_add_reuses_single_blank_draft(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    from tasker.shell.window import DockWindow

    store = Store(tmp_path / "tasker.sqlite")
    dock = DockWindow(store)
    qtbot.addWidget(dock)
    dock.add_btn.click()
    dock.add_btn.click()
    assert len(store.list_visible()) == 1
    item = store.list_visible()[0]
    store.save(replace(item, title="第一条"))
    dock.add_btn.click()
    assert len(store.list_visible()) == 2


def test_dock_is_paper_not_white_plates(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    from tasker.shell.window import DockWindow

    css = dock_style()
    assert "background:white" not in css.replace(" ", "")
    assert PAPER in css
    assert "border-radius:16px" in css
    dock = DockWindow(Store(tmp_path / "tasker.sqlite"))
    qtbot.addWidget(dock)
    assert dock.pin_btn.text() == ""
    assert not dock.pin_btn.icon().isNull()
    assert dock.close_btn.text() == "×"
    assert dock.search.styleSheet() == "" or "white" not in dock.styleSheet()
    assert PAPER in dock.styleSheet()
    assert dock.chrome.layout().itemAt(0).widget() is dock.search
    assert "事项" not in [w.text() for w in dock.chrome.findChildren(QLabel)]


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
    assert dock._detail.delete_btn.text() == "删除"
    dock._detail.title_edit.setText("可关闭的任务")
    dock._detail.begin_write()
    dock._detail.journal.head_edit().setPlainText("正文")
    dock._detail.save_keep_open()
    loaded = store.get(item.id)
    assert loaded is not None
    assert loaded.title == "可关闭的任务"
    assert loaded.body_md
    assert "正文" in loaded.body_md
    dock._detail.close_detail()
    assert not dock._detail.isVisible()


def test_title_click_opens_detail_and_delete_removes_item(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    from tasker.shell.window import DockWindow

    store = Store(tmp_path / "tasker.sqlite")
    item = store.save(replace(store.create(), title="点开我"))
    dock = DockWindow(store)
    qtbot.addWidget(dock)
    card = dock.list_layout.itemAt(0).widget()
    qtbot.mouseClick(card, Qt.MouseButton.LeftButton)
    assert dock._detail is not None
    assert dock._detail.isVisible()
    assert dock._detail.delete_btn.text() == "删除"
    dock._detail.delete_btn.click()
    assert store.get(item.id) is None
    assert not dock._detail.isVisible()
    assert dock.list_layout.count() == 0


def test_empty_notes_collapse_to_one(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    from tasker.shell.window import DockWindow

    store = Store(tmp_path / "tasker.sqlite")
    store.create()
    store.create()
    dock = DockWindow(store)
    qtbot.addWidget(dock)
    assert dock.list_layout.count() == 1
    dock.add_btn.click()
    assert dock.list_layout.count() == 1


def test_note_keeps_dot_beside_title(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    from tasker.shell.window import DockWindow

    store = Store(tmp_path / "tasker.sqlite")
    store.save(replace(store.create(), title="对齐便签"))
    dock = DockWindow(store)
    qtbot.addWidget(dock)
    dock.resize(400, 800)
    dock.show()
    card = dock.list_layout.itemAt(0).widget()
    assert card.sizePolicy().verticalPolicy() == QSizePolicy.Policy.Maximum
    assert card.height() < 180
    assert card.importance.x() < card.title.x()
    assert abs(card.importance.y() - card.title.y()) < 10


def test_detail_is_embedded_and_follows_dock_move(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    from tasker.shell.window import DockWindow

    store = Store(tmp_path / "tasker.sqlite")
    item = store.save(replace(store.create(), title="跟着走"))
    dock = DockWindow(store)
    qtbot.addWidget(dock)
    dock.show()
    collapsed = dock.width()
    dock.open_detail(item.id)
    assert dock._detail is not None
    assert dock._detail.parent() is dock.detail_host
    assert dock.detail_host.isVisible()
    assert dock.width() > collapsed
    origin = dock._detail.mapToGlobal(QPoint(0, 0))
    dock.move(dock.pos() + QPoint(40, 24))
    qtbot.wait(20)
    assert dock._detail.mapToGlobal(QPoint(0, 0)) == origin + QPoint(40, 24)
    dock._detail.close_detail()
    assert not dock.detail_host.isVisible()
    assert not dock._detail.isVisible()
    assert dock.width() == collapsed


def test_close_button_hides_dock(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    from tasker.shell.window import DockWindow

    dock = DockWindow(Store(tmp_path / "tasker.sqlite"))
    qtbot.addWidget(dock)
    dock.show()
    assert dock.windowFlags() & Qt.WindowType.FramelessWindowHint
    assert dock.close_btn.text() == "×"
    dock.close_btn.click()
    assert not dock.isVisible()

