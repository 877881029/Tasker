from dataclasses import replace

from PySide6.QtCore import QEvent, QPoint, QRect, QSize, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QLabel, QSizePolicy, QToolButton

from tasker.shell.window import (
    default_extra_width,
    edge_hit,
    expand_from_dock,
    geometry_for_screen,
    paper_action,
)
from tasker.store import Store
from tasker.theme import DONE_BG, PAPER, dock_style


def test_geometry_is_right_third():
    avail = QRect(0, 0, 1200, 800)
    geo = geometry_for_screen(avail)
    assert geo.width() == 400
    assert geo.x() == 800
    assert geo.height() == 800


def test_expand_from_dock_grows_left_by_extra():
    avail = QRect(0, 0, 1920, 1080)
    collapsed = QRect(1000, 40, 400, 800)
    geo = expand_from_dock(collapsed, 800, avail)
    assert geo == QRect(200, 40, 1200, 800)
    assert geo.x() + geo.width() == collapsed.x() + collapsed.width()
    assert geo.y() == collapsed.y()
    assert geo.height() == collapsed.height()


def test_expand_from_dock_clamps_to_screen_left():
    avail = QRect(0, 0, 1920, 1080)
    collapsed = QRect(300, 80, 400, 700)
    geo = expand_from_dock(collapsed, 800, avail)
    assert geo == QRect(0, 80, 700, 700)


def test_expand_from_dock_zero_extra_when_on_left_edge():
    avail = QRect(0, 0, 1920, 1080)
    collapsed = QRect(0, 20, 400, 600)
    geo = expand_from_dock(collapsed, 800, avail)
    assert geo == collapsed


def test_default_extra_width_is_twice_rail():
    assert default_extra_width(QRect(100, 0, 400, 800)) == 800


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
    cursor = dock._detail.journal.head_edit().textCursor()
    cursor.insertText("正文")
    dock._detail.journal.head_edit().setTextCursor(cursor)
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


def test_open_detail_does_not_move_parked_rail(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    from tasker.shell.window import DockWindow

    store = Store(tmp_path / "tasker.sqlite")
    item = store.save(replace(store.create(), title="停在这"))
    dock = DockWindow(store)
    qtbot.addWidget(dock)
    dock.show()
    avail = QGuiApplication.primaryScreen().availableGeometry()
    parked = QRect(avail.x() + max(avail.width() - 480, 720), avail.y() + 80, 400, 640)
    dock.setGeometry(parked)
    qtbot.wait(20)
    parked = QRect(dock.geometry())
    dock.open_detail(item.id)
    qtbot.wait(20)
    expected = expand_from_dock(parked, default_extra_width(parked), avail)
    assert dock.geometry() == expected
    assert dock.x() + dock.width() == parked.x() + parked.width()
    assert dock.y() == parked.y()
    assert dock.height() == parked.height()
    assert dock.rail.width() == parked.width()
    dock._detail.close_detail()
    qtbot.wait(20)
    assert dock.geometry() == parked


def test_open_detail_reuses_resized_extra_width(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    from tasker.shell.window import DockWindow

    store = Store(tmp_path / "tasker.sqlite")
    item = store.save(replace(store.create(), title="记住宽"))
    dock = DockWindow(store)
    qtbot.addWidget(dock)
    dock.show()
    avail = QGuiApplication.primaryScreen().availableGeometry()
    parked = QRect(avail.x() + max(avail.width() - 480, 900), avail.y() + 80, 360, 600)
    dock.setGeometry(parked)
    qtbot.wait(20)
    parked = QRect(dock.geometry())
    dock.open_detail(item.id)
    qtbot.wait(20)
    extra = 500
    resized = expand_from_dock(parked, extra, avail)
    dock.setGeometry(resized)
    qtbot.wait(20)
    dock._detail.close_detail()
    qtbot.wait(20)
    dock.open_detail(item.id)
    qtbot.wait(20)
    assert dock.geometry() == expand_from_dock(parked, extra, avail)
    assert dock.x() + dock.width() == parked.x() + parked.width()
    assert dock.rail.width() == parked.width()


def test_closing_detail_keeps_moved_dock_position(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    from tasker.shell.window import DockWindow

    store = Store(tmp_path / "tasker.sqlite")
    item = store.save(replace(store.create(), title="别弹回去"))
    dock = DockWindow(store)
    qtbot.addWidget(dock)
    dock.show()
    collapsed = dock.width()
    parked = dock.pos() + QPoint(64, 48)
    dock.move(parked)
    qtbot.wait(20)
    dock.open_detail(item.id)
    qtbot.wait(20)
    assert dock.x() + dock.width() == parked.x() + collapsed
    assert dock.y() == parked.y()
    dock._detail.close_detail()
    qtbot.wait(20)
    assert dock.pos() == parked
    assert dock.width() == collapsed


def test_close_button_hides_dock(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    from tasker.shell.window import DockWindow

    dock = DockWindow(Store(tmp_path / "tasker.sqlite"))
    qtbot.addWidget(dock)
    dock.show()
    assert dock.windowFlags() & Qt.WindowType.FramelessWindowHint
    assert dock.windowFlags() & Qt.WindowType.Tool
    assert dock.close_btn.text() == "×"
    dock.close_btn.click()
    assert not dock.isVisible()
    assert dock.tray is not None


def test_dock_keeps_tray_icon(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    from PySide6.QtWidgets import QSystemTrayIcon
    from tasker.shell.window import DockWindow

    dock = DockWindow(Store(tmp_path / "tasker.sqlite"))
    qtbot.addWidget(dock)
    assert isinstance(dock.tray, QSystemTrayIcon)
    assert not dock.tray.icon().isNull()


def test_edge_hit_eight_ways():
    size = QSize(400, 300)
    assert edge_hit(QPoint(2, 150), size) & Qt.Edge.LeftEdge
    assert edge_hit(QPoint(398, 150), size) & Qt.Edge.RightEdge
    assert edge_hit(QPoint(200, 2), size) & Qt.Edge.TopEdge
    assert edge_hit(QPoint(200, 298), size) & Qt.Edge.BottomEdge
    corners = edge_hit(QPoint(1, 1), size)
    assert corners & Qt.Edge.LeftEdge and corners & Qt.Edge.TopEdge
    assert not bool(edge_hit(QPoint(200, 150), size))


def test_paper_action_move_resize_or_ignore():
    size = QSize(400, 300)
    assert paper_action(QPoint(2, 150), size, "search") == "resize"
    assert paper_action(QPoint(200, 150), size, "listHost") == "move"
    assert paper_action(QPoint(200, 150), size, "chrome") == "move"
    assert paper_action(QPoint(200, 150), size, "search") == "ignore"
    assert paper_action(QPoint(200, 150), size, "itemCard") == "ignore"
    assert paper_action(QPoint(200, 150), size, "journalDocument") == "ignore"

