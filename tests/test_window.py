import pathlib
from dataclasses import replace

from PySide6.QtCore import QEvent, QPoint, QRect, QSize, Qt
from PySide6.QtGui import QGuiApplication, QPalette
from PySide6.QtWidgets import QLabel, QSizePolicy, QToolButton

from tasker.shell.window import (
    HTBOTTOM,
    HTBOTTOMLEFT,
    HTBOTTOMRIGHT,
    HTCLIENT,
    HTLEFT,
    HTRIGHT,
    HTTOP,
    HTTOPLEFT,
    HTTOPRIGHT,
    default_extra_width,
    edge_hit,
    expand_from_dock,
    geometry_for_screen,
    hit_test_local,
    paper_action,
    fit_into,
    paper_corner_radius,
    split_rail_width,
)
from tasker.store import Store
from tasker.theme import CHROME, DONE_DOT, HOVER, LINE, PAPER, SELECTED, dock_style


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


def test_expand_from_dock_shifts_right_when_left_room_is_short():
    avail = QRect(0, 0, 1920, 1080)
    collapsed = QRect(300, 80, 400, 700)
    geo = expand_from_dock(collapsed, 800, avail)
    assert geo == QRect(0, 80, 1200, 700)


def test_expand_from_dock_on_left_edge_still_opens_detail():
    avail = QRect(0, 0, 1920, 1080)
    collapsed = QRect(0, 20, 400, 600)
    geo = expand_from_dock(collapsed, 800, avail)
    assert geo == QRect(0, 20, 1200, 600)


def test_expand_from_dock_keeps_minimum_detail_and_stays_on_screen():
    avail = QRect(1920, 0, 1280, 1000)
    collapsed = QRect(2600, 900, 400, 600)
    geo = expand_from_dock(collapsed, 100, avail)
    assert geo.width() == 400 + 360
    assert avail.contains(geo)
    narrow = expand_from_dock(QRect(0, 0, 400, 500), 2000, QRect(0, 0, 900, 600))
    assert narrow == QRect(0, 0, 900, 500)


def test_default_extra_width_is_twice_rail():
    assert default_extra_width(QRect(100, 0, 400, 800)) == 800
    assert default_extra_width(QRect(100, 0, 120, 800)) == 360


def test_fit_into_pulls_window_back_on_screen():
    avail = QRect(0, 40, 1600, 860)
    assert fit_into(QRect(100, 100, 400, 500), avail) == QRect(100, 100, 400, 500)
    assert fit_into(QRect(2500, 100, 400, 500), avail) == QRect(1200, 100, 400, 500)
    assert fit_into(QRect(-900, -50, 400, 500), avail) == QRect(0, 40, 400, 500)
    assert fit_into(QRect(10, 10, 2400, 1200), avail) == avail


def test_split_rail_width_respects_both_minimums():
    assert split_rail_width(1200, 400) == 400
    assert split_rail_width(1200, 100) == 280
    assert split_rail_width(1200, 1100) == 1200 - 7 - 360
    assert split_rail_width(500, 400) == 280


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
    dock._detail.set_status("urgent")
    item = store.get(only.item_id)
    assert item is not None and item.state == "urgent"
    only = dock.list_layout.itemAt(0).widget()
    assert getattr(only, "done", None) is None
    assert only.findChild(QToolButton, "openDetail") is None
    assert "border-radius:5px" in only.importance.styleSheet()
    assert only.importance.size() == QSize(10, 10)
    assert only.minimumHeight() == 40
    assert only.is_selected()
    assert SELECTED in only.styleSheet()
    dock._detail.set_status("done")
    item = store.get(only.item_id)
    assert item is not None and item.state == "done"
    dock._detail.close_detail()
    dock.done_toggle().click()
    only = dock.cards()[0]
    assert DONE_DOT in only.importance.styleSheet()
    assert not only.is_selected()
    assert HOVER in only.styleSheet()
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
    assert PAPER in css and CHROME in css
    assert "border-radius:10px" in css
    dock = DockWindow(Store(tmp_path / "tasker.sqlite"))
    qtbot.addWidget(dock)
    assert dock.testAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
    assert dock.pin_btn.text() == ""
    assert not dock.pin_btn.icon().isNull()
    assert dock.add_btn.text() == ""
    assert not dock.add_btn.icon().isNull()
    assert dock.view_btn.text() == ""
    assert not dock.view_btn.icon().isNull()
    assert dock.view_btn.toolTip() == "显示最新日志摘要"
    assert not dock.search.hasFrame()
    assert dock.search.height() == 34
    assert len(dock.search.actions()) == 1
    assert not dock.search.actions()[0].icon().isNull()
    assert dock.search.palette().color(QPalette.ColorRole.Base).name() == "#fdfbf9"
    assert dock.search.palette().color(QPalette.ColorRole.PlaceholderText).name() == "#6b655f"
    assert dock.add_btn.size() == QSize(32, 32)
    assert dock.pin_btn.size() == QSize(32, 32)
    assert dock.view_btn.size() == QSize(32, 32)
    assert dock.search.styleSheet() == "" or "white" not in dock.styleSheet()
    assert PAPER in dock.styleSheet()
    assert dock.chrome.layout().itemAt(0).widget() is dock.search
    assert "事项" not in [w.text() for w in dock.chrome.findChildren(QLabel)]


def test_empty_and_search_states_are_distinct(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    from tasker.shell.window import DockWindow

    store = Store(tmp_path / "tasker.sqlite")
    dock = DockWindow(store)
    qtbot.addWidget(dock)

    empty = dock.findChild(QLabel, "emptyState")
    assert empty is not None
    assert "还没有事项" in empty.text()
    assert "点 + 开始记录" in empty.text()
    assert empty.focusPolicy() == Qt.FocusPolicy.NoFocus
    assert store.list_visible() == []

    store.save(replace(store.create(), title="PDF 默认应用"))
    dock.refresh()
    assert dock.findChild(QLabel, "emptyState") is None

    dock.search.setText("不存在")
    no_match = dock.findChild(QLabel, "emptyState")
    assert no_match is not None
    assert "没有找到匹配事项" in no_match.text()
    assert "换个关键词试试" in no_match.text()
    assert len(store.list_visible()) == 1

    dock.search.setText("PDF")
    assert dock.findChild(QLabel, "emptyState") is None
    assert dock.list_layout.count() == 1


def test_cards_and_rail_tools_are_keyboard_and_accessibility_ready(
    qtbot, tmp_path, monkeypatch
):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    from tasker.shell.window import DockWindow

    store = Store(tmp_path / "tasker.sqlite")
    item = store.save(replace(store.create(), title="键盘打开"))
    dock = DockWindow(store)
    qtbot.addWidget(dock)
    dock.show()
    card = dock.list_layout.itemAt(0).widget()

    assert card.focusPolicy() == Qt.FocusPolicy.StrongFocus
    assert "普通任务" in card.accessibleName()
    assert "键盘打开" in card.accessibleName()
    assert "Enter" in card.accessibleDescription()
    assert "普通" in card.toolTip()
    assert dock.add_btn.accessibleName() == "新建事项"
    assert dock.pin_btn.accessibleName() == "置顶窗口"
    assert dock.view_btn.accessibleName() == "显示日志摘要"
    assert dock.settings_btn.nextInFocusChain() is card
    assert "QWidget#itemCard:focus" in dock_style()
    assert "QToolButton#addBtn:focus" in dock_style()

    card.setFocus()
    qtbot.keyClick(card, Qt.Key.Key_Return)
    assert dock._detail is not None and dock._detail.isVisible()
    assert dock._open_item_id == item.id
    dock._detail.close_detail()

    card = dock.list_layout.itemAt(0).widget()
    card.setFocus()
    qtbot.keyClick(card, Qt.Key.Key_Space)
    assert dock._detail.isVisible()


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
    assert dock.findChild(QLabel, "emptyState") is not None


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
    dock.resize(400, dock.height() - 96)
    qtbot.wait(20)
    collapsed = dock.width()
    parked = dock.pos() + QPoint(-64, 48)
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


def test_escape_hides_dock_and_view_toggle_replaces_close(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    from tasker.shell.window import DockWindow

    dock = DockWindow(Store(tmp_path / "tasker.sqlite"))
    qtbot.addWidget(dock)
    dock.show()
    assert dock.windowFlags() & Qt.WindowType.FramelessWindowHint
    assert dock.windowFlags() & Qt.WindowType.Tool
    assert getattr(dock, "close_btn", None) is None
    assert dock.view_btn.isCheckable()
    dock.escape()
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
    assert paper_action(QPoint(200, 150), size, "detail") == "move"
    assert paper_action(QPoint(200, 150), size, "detailFooter") == "move"
    assert paper_action(QPoint(200, 150), size, "detailTitle") == "ignore"
    assert paper_action(QPoint(200, 150), size, "notch") == "split"


def test_paper_corner_radius_is_zero_when_flush_to_work_area():
    avail = QRect(0, 40, 1920, 1040)
    inset = QRect(200, 80, 1200, 800)
    assert paper_corner_radius(inset, avail) == 10
    assert paper_corner_radius(avail, avail) == 0
    assert paper_corner_radius(QRect(1, 41, 1918, 1038), avail) == 0


def test_hit_test_local_eight_edges():
    size = QSize(400, 300)
    assert hit_test_local(size, QPoint(2, 150)) == HTLEFT
    assert hit_test_local(size, QPoint(398, 150)) == HTRIGHT
    assert hit_test_local(size, QPoint(200, 2)) == HTTOP
    assert hit_test_local(size, QPoint(200, 298)) == HTBOTTOM
    assert hit_test_local(size, QPoint(1, 1)) == HTTOPLEFT
    assert hit_test_local(size, QPoint(399, 1)) == HTTOPRIGHT
    assert hit_test_local(size, QPoint(1, 299)) == HTBOTTOMLEFT
    assert hit_test_local(size, QPoint(399, 299)) == HTBOTTOMRIGHT
    assert hit_test_local(size, QPoint(200, 150)) == HTCLIENT


def test_fill_work_area_keeps_rail_and_stretches_detail(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    from tasker.shell.window import DockWindow

    store = Store(tmp_path / "tasker.sqlite")
    item = store.save(replace(store.create(), title="铺满"))
    dock = DockWindow(store)
    qtbot.addWidget(dock)
    dock.show()
    avail = QGuiApplication.primaryScreen().availableGeometry()
    parked = QRect(avail.x() + avail.width() - 400, avail.y() + 80, 400, 640)
    dock.setGeometry(parked)
    qtbot.wait(20)
    parked = QRect(dock.geometry())
    dock.open_detail(item.id)
    qtbot.wait(20)
    dock.setGeometry(avail)
    qtbot.wait(20)
    assert dock.rail.width() == parked.width()
    assert dock.x() + dock.width() == avail.x() + avail.width()
    leftover = dock.width() - dock.rail.width() - dock.notch.width()
    assert dock.detail_host.width() >= leftover - 8
    assert paper_corner_radius(dock.geometry(), avail) == 0
    assert dock.mask().isEmpty() or dock.mask().boundingRect().size() == dock.size()


def test_open_detail_keeps_cards_and_marks_selection(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    from tasker.shell.window import DockWindow

    store = Store(tmp_path / "tasker.sqlite")
    first = store.save(replace(store.create(), title="一"))
    second = store.save(replace(store.create(), title="二"))
    dock = DockWindow(store)
    qtbot.addWidget(dock)
    dock.show()
    before = dock.cards()
    dock.open_detail(first.id)
    assert dock.cards() == before
    selected = [card.item_id for card in dock.cards() if card.is_selected()]
    assert selected == [first.id]
    dock.open_detail(second.id)
    assert dock.cards() == before
    selected = [card.item_id for card in dock.cards() if card.is_selected()]
    assert selected == [second.id]
    assert dock.notch.width() == 7
    assert dock.notch.line_color == LINE
    assert dock.notch.cursor().shape() == Qt.CursorShape.SplitHCursor


def test_card_status_menu_changes_state_and_syncs_detail(qtbot, tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    from tasker.shell.window import DockWindow

    store = Store(tmp_path / "tasker.sqlite")
    item = store.save(replace(store.create(), title="右键"))
    dock = DockWindow(store)
    qtbot.addWidget(dock)
    dock.show()
    dock.open_detail(item.id)
    card = dock.cards()[0]
    menu = card.status_menu()
    assert [a.text() for a in menu.actions()] == ["普通", "紧急", "已完成"]
    assert menu.actions()[0].isChecked()
    assert menu.windowFlags() & Qt.WindowType.FramelessWindowHint
    menu.actions()[2].trigger()
    assert store.get(item.id).state == "done"
    assert dock._detail.status_btn.text().startswith("已完成")
    assert DONE_DOT in dock.cards()[0].importance.styleSheet()
    assert dock.tray.contextMenu().objectName() == "trayMenu"


def test_pin_icon_is_a_pushpin_that_fills_when_pinned(qtbot, tmp_path):
    from PySide6.QtGui import QIcon

    from tasker.shell.window import DockWindow
    from tasker.store import Store
    from tasker.theme import COBALT, INK

    dock = DockWindow(Store(tmp_path / "tasker.sqlite"))
    qtbot.addWidget(dock)
    icon = dock.pin_btn.icon()
    off = icon.pixmap(QSize(32, 32), QIcon.Mode.Normal, QIcon.State.Off).toImage()
    on = icon.pixmap(QSize(32, 32), QIcon.Mode.Normal, QIcon.State.On).toImage()
    assert off != on
    root = pathlib.Path(__file__).resolve().parents[1] / "assets" / "icons"
    assert INK.lower() in (root / "pin.svg").read_text(encoding="utf-8").lower()
    on_svg = (root / "pin-on.svg").read_text(encoding="utf-8").lower()
    assert COBALT.lower() in on_svg and 'fill="none"' not in on_svg.split("<path")[0]


def _dock_with_item(qtbot, tmp_path, monkeypatch, title="窗口"):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    from tasker.shell.window import DockWindow

    store = Store(tmp_path / "tasker.sqlite")
    item = store.save(replace(store.create(), title=title))
    dock = DockWindow(store)
    qtbot.addWidget(dock)
    dock.show()
    return dock, item


def test_open_detail_on_left_edge_keeps_detail_usable(qtbot, tmp_path, monkeypatch):
    dock, item = _dock_with_item(qtbot, tmp_path, monkeypatch)
    avail = dock.work_area()
    parked = QRect(avail.x(), avail.y() + 40, 400, 600)
    dock.setGeometry(parked)
    qtbot.wait(20)
    parked = QRect(dock.geometry())
    dock.open_detail(item.id)
    qtbot.wait(20)
    assert avail.contains(dock.geometry())
    assert dock.detail_host.width() >= 360
    assert dock.minimumWidth() >= dock.rail.width() + 360
    dock._detail.close_detail()
    qtbot.wait(20)
    assert dock.geometry() == parked


def test_fit_to_screen_recovers_offscreen_window(qtbot, tmp_path, monkeypatch):
    dock, _item = _dock_with_item(qtbot, tmp_path, monkeypatch)
    avail = dock.work_area()
    dock.setGeometry(QRect(avail.right() + 600, avail.y(), 400, 500))
    dock._fit_to_screen()
    qtbot.wait(20)
    assert avail.intersects(dock.geometry())
    assert avail.contains(dock.geometry())


def test_toggle_fill_maximizes_and_restores(qtbot, tmp_path, monkeypatch):
    from PySide6.QtCore import QPointF
    from PySide6.QtGui import QMouseEvent
    from PySide6.QtWidgets import QApplication

    dock, _item = _dock_with_item(qtbot, tmp_path, monkeypatch)
    avail = dock.work_area()
    start = QRect(avail.x() + 100, avail.y() + 60, 400, 500)
    dock.setGeometry(start)
    qtbot.wait(20)
    start = QRect(dock.geometry())
    dock.toggle_fill()
    qtbot.wait(20)
    assert dock.geometry() == avail
    assert dock.corner_overlay.radius() == 0
    pos = QPointF(dock.chrome.width() - 6, dock.chrome.height() / 2)
    dbl = QMouseEvent(
        QEvent.Type.MouseButtonDblClick,
        pos,
        QPointF(dock.chrome.mapToGlobal(pos.toPoint())),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(dock.chrome, dbl)
    qtbot.wait(20)
    assert dock.geometry() == start
    assert dock.corner_overlay.radius() == 10


def test_corner_overlay_replaces_window_mask(qtbot, tmp_path, monkeypatch):
    dock, _item = _dock_with_item(qtbot, tmp_path, monkeypatch)
    overlay = dock.corner_overlay
    assert overlay.objectName() == "cornerOverlay"
    assert overlay.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    assert overlay.geometry() == dock.rect()
    assert dock.mask().isEmpty()


def test_rail_width_drag_changes_split_and_is_remembered(qtbot, tmp_path, monkeypatch):
    dock, item = _dock_with_item(qtbot, tmp_path, monkeypatch)
    avail = dock.work_area()
    dock.setGeometry(QRect(avail.right() - 420, avail.y() + 40, 420, 600))
    qtbot.wait(20)
    dock.open_detail(item.id)
    qtbot.wait(20)
    total = dock.width()
    dock.set_rail_width(320)
    qtbot.wait(20)
    assert dock.rail.width() == 320
    assert dock.width() == total
    dock._detail.close_detail()
    qtbot.wait(20)
    assert dock.width() == 320


def test_stylesheets_parse_cleanly(qtbot, tmp_path, monkeypatch):
    import re

    from PySide6.QtCore import qInstallMessageHandler

    from tasker.shell.journal_edit import journal_document_html

    style = re.search(r"<style>(.*?)</style>", journal_document_html([], writable=True), re.S)
    assert style is not None
    depth = 0
    for char in style.group(1):
        depth += {"{": 1, "}": -1}.get(char, 0)
        assert depth >= 0
    assert depth == 0

    messages: list[str] = []
    previous = qInstallMessageHandler(lambda _kind, _ctx, text: messages.append(text))
    try:
        dock, item = _dock_with_item(qtbot, tmp_path, monkeypatch)
        dock.open_detail(item.id)
        detail = dock._detail
        detail.delete_item()
        for widget in (dock, detail, detail.status_btn, detail.delete_btn):
            widget.ensurePolished()
        qtbot.wait(20)
    finally:
        qInstallMessageHandler(previous)
    assert not [m for m in messages if "Could not parse stylesheet" in m]
