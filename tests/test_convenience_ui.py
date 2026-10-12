from dataclasses import replace
from datetime import datetime, timedelta

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

from tasker.store import Store


def _dock(qtbot, tmp_path, monkeypatch, *specs):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    from tasker.shell.window import DockWindow

    store = Store(tmp_path)
    items = []
    for title, state, body in specs:
        items.append(
            store.save(
                replace(store.create(), title=title, state=state, resume_state=state, body_md=body)
            )
        )
    dock = DockWindow(store)
    qtbot.addWidget(dock)
    dock.show()
    return dock, store, items


def test_done_items_collapse_behind_toggle(qtbot, tmp_path, monkeypatch):
    dock, _store, (a, b) = _dock(
        qtbot, tmp_path, monkeypatch, ("进行", "pending", ""), ("完了", "done", "")
    )
    assert [card.item_id for card in dock.cards()] == [a.id]
    toggle = dock.done_toggle()
    assert toggle is not None and toggle.text().startswith("已完成 (1)")
    toggle.click()
    assert [card.item_id for card in dock.cards()] == [a.id, b.id]
    dock.done_toggle().click()
    assert [card.item_id for card in dock.cards()] == [a.id]
    dock.search.setText("完了")
    assert [card.item_id for card in dock.cards()] == [b.id]


def test_no_done_toggle_without_done_items(qtbot, tmp_path, monkeypatch):
    dock, _store, _items = _dock(qtbot, tmp_path, monkeypatch, ("进行", "pending", ""))
    assert dock.done_toggle() is None


def test_summary_line_shows_latest_log(qtbot, tmp_path, monkeypatch):
    body = "261012.3PM\n\n最新进展\n第二行\n\n261011.3PM\n\n旧的"
    dock, _store, (a, b) = _dock(
        qtbot, tmp_path, monkeypatch, ("有日志", "pending", body), ("无日志", "pending", "")
    )
    cards = {card.item_id: card for card in dock.cards()}
    assert cards[a.id].summary.fullText() == "最新进展"
    assert not cards[a.id].summary.isHidden()
    assert cards[b.id].summary.isHidden()


def test_card_context_menu_sets_deadline(qtbot, tmp_path, monkeypatch):
    dock, store, (a, b) = _dock(
        qtbot, tmp_path, monkeypatch, ("紧", "urgent", ""), ("普", "pending", "")
    )
    cards = {card.item_id: card for card in dock.cards()}
    plain_menu = cards[b.id].status_menu()
    assert [x.text() for x in plain_menu.actions()] == ["普通", "紧急", "已完成"]
    menu = cards[a.id].status_menu()
    sub = [x for x in menu.actions() if x.menu() is not None]
    assert len(sub) == 1 and sub[0].text() == "DDL"
    dock.open_detail(a.id)
    picks = [x for x in sub[0].menu().actions() if x.text().startswith("明天")]
    picks[0].trigger()
    assert store.get(a.id).deadline is not None
    assert dock._detail.deadline_btn.text().startswith("DDL ")
    card = next(card for card in dock.cards() if card.item_id == a.id)
    assert not card.deadline_pill.isHidden()


def test_delete_key_removes_and_undo_restores(qtbot, tmp_path, monkeypatch):
    dock, store, (a, b) = _dock(
        qtbot, tmp_path, monkeypatch, ("一", "pending", "261012.3PM\n\n内容"), ("二", "pending", "")
    )
    card = next(card for card in dock.cards() if card.item_id == a.id)
    card.setFocus()
    qtbot.keyClick(card, Qt.Key.Key_Delete)
    assert store.get(a.id) is None
    assert dock.toast.isVisibleTo(dock.rail)
    assert "已删除「一」" in dock.toast.text.fullText()
    dock.toast.action.click()
    restored = store.get(a.id)
    assert restored is not None and "内容" in restored.body_md
    assert not dock.toast.isVisibleTo(dock.rail)
    assert a.id in [card.item_id for card in dock.cards()]


def test_detail_delete_offers_undo_and_ctrl_z(qtbot, tmp_path, monkeypatch):
    dock, store, (a,) = _dock(qtbot, tmp_path, monkeypatch, ("删我", "urgent", ""))
    dock.open_detail(a.id)
    dock._detail.delete_btn.click()
    assert store.get(a.id) is None
    assert "删我" in dock.toast.text.fullText()
    dock.undo_delete()
    assert store.get(a.id) is not None
    dock.undo_delete()
    assert store.get(a.id) is not None


def test_undo_expires(qtbot, tmp_path, monkeypatch):
    dock, store, (a,) = _dock(qtbot, tmp_path, monkeypatch, ("过期", "pending", ""))
    dock.delete_item(a.id)
    dock.toast.dismiss()
    dock.undo_delete()
    assert store.get(a.id) is None


def test_arrow_navigation_between_search_and_cards(qtbot, tmp_path, monkeypatch):
    dock, _store, (a, b) = _dock(
        qtbot, tmp_path, monkeypatch, ("一", "urgent", ""), ("二", "pending", "")
    )
    dock.activateWindow()
    qtbot.waitUntil(dock.isActiveWindow, timeout=1000)
    dock.search.setFocus()
    qtbot.keyClick(dock.search, Qt.Key.Key_Down)
    first, second = dock.cards()
    assert first.hasFocus()
    qtbot.keyClick(first, Qt.Key.Key_Down)
    assert second.hasFocus()
    qtbot.keyClick(second, Qt.Key.Key_Up)
    qtbot.keyClick(first, Qt.Key.Key_Up)
    assert dock.search.hasFocus()


def test_escape_hides_to_tray_unless_pinned(qtbot, tmp_path, monkeypatch):
    dock, _store, (a,) = _dock(qtbot, tmp_path, monkeypatch, ("一", "pending", ""))
    dock.search.setText("x")
    dock.escape()
    assert dock.search.text() == "" and dock.isVisible()
    dock.pin_btn.setChecked(True)
    dock.escape()
    assert dock.isVisible()
    dock.pin_btn.setChecked(False)
    dock.show()
    qtbot.keyClick(dock.search, Qt.Key.Key_Escape)
    assert not dock.isVisible()


def test_escape_with_detail_open_only_closes_detail(qtbot, tmp_path, monkeypatch):
    dock, _store, (a,) = _dock(qtbot, tmp_path, monkeypatch, ("一", "pending", ""))
    dock.open_detail(a.id)
    dock._detail.close_detail()
    assert dock.isVisible()
    assert not dock.detail_host.isVisible()


def test_copy_weekly_report_to_clipboard(qtbot, tmp_path, monkeypatch):
    now = datetime.now()
    from tasker.journal import stamp_for

    body = f"{stamp_for(now)}\n\n今天做了"
    dock, _store, _items = _dock(qtbot, tmp_path, monkeypatch, ("周报项", "pending", body))
    dock.copy_weekly_report()
    text = QGuiApplication.clipboard().text()
    assert text.startswith("# 周报") and "### 周报项" in text and "今天做了" in text
    assert "已复制本周周报" in dock.toast.text.fullText()


def test_quick_capture_creates_task_without_detail(qtbot, tmp_path, monkeypatch):
    dock, store, _items = _dock(qtbot, tmp_path, monkeypatch)
    dock.quick_capture()
    quick = dock._quick
    qtbot.addWidget(quick)
    quick.edit.setText("!修复回归")
    qtbot.keyClick(quick.edit, Qt.Key.Key_Return)
    assert not quick.isVisible()
    items = store.list_visible("")
    assert [(i.title, i.state) for i in items] == [("修复回归", "urgent")]
    assert not dock.detail_host.isVisible()
    assert dock.cards()[0].item_id == items[0].id
    dock.quick_capture()
    qtbot.keyClick(quick.edit, Qt.Key.Key_Escape)
    assert len(store.list_visible("")) == 1


def test_overdue_badge_and_tray_menu(qtbot, tmp_path, monkeypatch):
    dock, store, (a,) = _dock(qtbot, tmp_path, monkeypatch, ("超", "urgent", ""))
    assert dock.badge() == ""
    store.set_deadline(a.id, datetime.now() - timedelta(minutes=5))
    dock.refresh()
    assert dock.badge() == "1"
    assert "1 个任务已超期" in dock.tray.toolTip()
    labels = [x.text() for x in dock.tray.contextMenu().actions() if x.text()]
    assert labels[:3] == ["显示", "快速记录", "复制本周周报"]
    assert "开机自启" in labels and labels[-1] == "退出"
    dock.set_hotkey_label("Win+Alt+T")
    assert dock.capture_action.text() == "快速记录（Win+Alt+T）"


def test_search_tooltip_lists_keywords(qtbot, tmp_path, monkeypatch):
    dock, _store, _items = _dock(qtbot, tmp_path, monkeypatch)
    assert "超期" in dock.search.toolTip()
    assert dock.search.placeholderText() == "查找任务或日志…"


def test_shortcuts_registered(qtbot, tmp_path, monkeypatch):
    dock, _store, _items = _dock(qtbot, tmp_path, monkeypatch)
    keys = {s.key().toString() for s in dock._shortcuts}
    assert {"Ctrl+N", "Ctrl+F", "Ctrl+Z", "Ctrl+Shift+C"} <= keys
    assert QApplication.instance() is not None
