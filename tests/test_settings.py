from dataclasses import replace
from datetime import datetime

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence

from tasker.safety import backup_tasks, daily_backup, list_backups, remove_file
from tasker.settings import SHORTCUTS, shortcut_conflict, shortcut_map
from tasker.shell.hotkey import MOD_ALT, MOD_CONTROL, MOD_SHIFT, MOD_WIN, parse_combo
from tasker.store import Store


# ---- pure helpers ----------------------------------------------------------

def test_parse_combo():
    assert parse_combo("Win+Alt+T") == (MOD_WIN | MOD_ALT, ord("T"))
    assert parse_combo("Ctrl+Shift+9") == (MOD_CONTROL | MOD_SHIFT, ord("9"))
    assert parse_combo("F9") == (0, 0x78)
    assert parse_combo("Meta+Q") == (MOD_WIN, ord("Q"))
    assert parse_combo("T") is None
    assert parse_combo("Ctrl+Space") is None
    assert parse_combo("Hyper+T") is None


def test_shortcut_conflicts():
    mapping = {action: spec[2] for action, spec in SHORTCUTS.items()}
    assert shortcut_conflict(mapping, "new", "Ctrl+F") == "与「查找」冲突"
    assert shortcut_conflict(mapping, "new", "Esc") is not None
    assert shortcut_conflict(mapping, "new", "N") is not None
    assert shortcut_conflict(mapping, "new", "F2") is None
    assert shortcut_conflict(mapping, "new", "Ctrl+Shift+N") is None
    assert shortcut_conflict(mapping, "new", "Ctrl+N") is None


def test_backup_rotation_and_daily(tmp_path):
    store = Store(tmp_path / "data")
    store.save(replace(store.create(), title="备份我"))
    dest = tmp_path / "bk"
    for day in range(1, 10):
        backup_tasks(store.root, dest, now=datetime(2026, 10, day, 9, 0))
    names = [p.name for p in list_backups(dest)]
    assert len(names) == 7 and names[0] == "tasker-20261003-090000.zip"
    import zipfile

    with zipfile.ZipFile(list_backups(dest)[-1]) as archive:
        assert any(name.startswith("tasks/") and name.endswith(".md") for name in archive.namelist())
    assert daily_backup(store.root, dest, now=datetime(2026, 10, 9, 18, 0)) is None
    assert daily_backup(store.root, dest, now=datetime(2026, 10, 10, 8, 0)) is not None


def test_remove_file_without_recycle(tmp_path, monkeypatch):
    monkeypatch.setenv("TASKER_NO_RECYCLE", "1")
    target = tmp_path / "x.md"
    target.write_text("x", encoding="utf-8")
    remove_file(target)
    assert not target.exists()
    remove_file(target)


def test_delete_uses_recycle_bin_when_enabled(tmp_path, monkeypatch):
    monkeypatch.delenv("TASKER_NO_RECYCLE", raising=False)
    sent = []
    monkeypatch.setattr("tasker.safety.send_to_recycle_bin", lambda p: sent.append(p) or (p.unlink() or True))
    store = Store(tmp_path)
    item = store.create()
    store.delete(item.id)
    assert sent and sent[0].name == f"{item.id}.md"
    draft = store.create()
    sent.clear()
    store.delete(draft.id, recycle=False)
    assert sent == []


# ---- dock / settings window -----------------------------------------------

def _dock(qtbot, tmp_path, monkeypatch, *titles):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("TASKER_BACKUP_DIR", str(tmp_path / "backups"))
    from tasker.shell.window import DockWindow

    store = Store(tmp_path)
    items = [store.save(replace(store.create(), title=t)) for t in titles]
    dock = DockWindow(store)
    qtbot.addWidget(dock)
    dock.show()
    return dock, store, items


def test_quit_saves_journal_being_written(qtbot, tmp_path, monkeypatch):
    dock, store, (item,) = _dock(qtbot, tmp_path, monkeypatch, "写到一半")
    dock.open_detail(item.id)
    dock._detail.begin_write()
    editor = dock._detail.journal.head_edit()
    cursor = editor.textCursor()
    cursor.insertText("退出前没保存的内容")
    editor.setTextCursor(cursor)
    quits = []
    monkeypatch.setattr("PySide6.QtWidgets.QApplication.quit", lambda *a: quits.append(1))
    dock._quit_app()
    assert quits
    assert "退出前没保存的内容" in store.get(item.id).body_md


def test_settings_button_and_tray_entry(qtbot, tmp_path, monkeypatch):
    dock, _store, _items = _dock(qtbot, tmp_path, monkeypatch)
    assert dock.settings_btn.objectName() == "settingsBtn"
    assert not dock.settings_btn.icon().isNull()
    labels = [a.text() for a in dock.tray.contextMenu().actions()]
    assert "设置…" in labels
    dock.settings_btn.click()
    win = dock._settings
    qtbot.addWidget(win)
    assert win.isVisible() and win.current_section() == "general"
    assert [b.text() for b in win.nav_buttons.values()] == ["通用", "快捷键", "功能说明", "数据"]
    win.nav_buttons["features"].click()
    assert win.current_section() == "features"


def test_settings_toggles_drive_app(qtbot, tmp_path, monkeypatch):
    from tasker.settings import get_setting

    dock, store, _items = _dock(qtbot, tmp_path, monkeypatch, "一")
    dock.open_settings()
    win = dock._settings
    qtbot.addWidget(win)
    win.toggles["summary"].click()
    assert dock.summary_mode() and dock.view_btn.isChecked()
    win.toggles["reminders"].click()
    assert get_setting(store.root, "reminders") is False
    win.toggles["auto_backup"].click()
    assert get_setting(store.root, "auto_backup") is False
    dock.view_btn.click()
    dock.open_settings()
    assert not win.toggles["summary"].isChecked()


def test_rebind_dock_and_detail_shortcuts(qtbot, tmp_path, monkeypatch):
    from tasker.shell.window import DockWindow

    dock, store, (item,) = _dock(qtbot, tmp_path, monkeypatch, "一")
    dock.open_settings("shortcuts")
    win = dock._settings
    qtbot.addWidget(win)
    assert win.current_section() == "shortcuts"
    win._capture("new", "Ctrl+Shift+N")
    assert dock._shortcut_by_action["new"].key() == QKeySequence("Ctrl+Shift+N")
    assert win.shortcut_fields["new"].text() == "Ctrl+Shift+N"
    win._capture("new", "Ctrl+F")
    assert "冲突" in win.rows["key:new"].error.text()
    assert dock.shortcut_keys()["new"] == "Ctrl+Shift+N"
    dock.open_detail(item.id)
    win._capture("write", "Ctrl+E")
    assert dock._detail._write_shortcut.key() == QKeySequence("Ctrl+E")
    assert dock._detail.journal_status.text().startswith("Ctrl+E 写入")
    again = DockWindow(store)
    qtbot.addWidget(again)
    assert again.shortcut_keys()["new"] == "Ctrl+Shift+N"
    win._reset()
    assert dock.shortcut_keys() == shortcut_map(store.root)
    assert dock._shortcut_by_action["new"].key() == QKeySequence("Ctrl+N")
    assert dock._detail.journal_status.text().startswith("Ctrl+I 写入")


def test_global_hotkey_rebind_failure_keeps_previous(qtbot, tmp_path, monkeypatch):
    class FakeHotkey:
        def __init__(self):
            self.label = ""

        def register(self, *_a):
            self.label = "Ctrl+Alt+T"
            return self.label

        def register_text(self, text):
            if text in ("", "Ctrl+Alt+T"):
                return self.register()
            if text == "Ctrl+Alt+K":
                self.label = text
                return text
            return ""

    dock, _store, _items = _dock(qtbot, tmp_path, monkeypatch)
    dock.attach_hotkey(FakeHotkey())
    assert dock.hotkey_label == "Ctrl+Alt+T"
    assert dock.apply_shortcut("quick_capture", "Ctrl+Alt+Q") is not None
    assert dock.hotkey_label == "Ctrl+Alt+T"
    assert dock.apply_shortcut("quick_capture", "Ctrl+Alt+K") is None
    assert dock.capture_action.text() == "快速记录（Ctrl+Alt+K）"


def test_shortcut_field_captures_keys(qtbot):
    from tasker.shell.settings_window import ShortcutField

    field = ShortcutField()
    qtbot.addWidget(field)
    got = []
    field.captured.connect(got.append)
    field.set_keys("Ctrl+N")
    field.click()
    assert field.text() == "按下新快捷键…"
    qtbot.keyClick(field, Qt.Key.Key_Control)
    qtbot.keyClick(field, Qt.Key.Key_K, Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)
    assert got == ["Ctrl+Shift+K"]
    field.click()
    qtbot.keyClick(field, Qt.Key.Key_Escape)
    assert not field.isChecked() and got == ["Ctrl+Shift+K"]


def test_data_section_backup_now(qtbot, tmp_path, monkeypatch):
    dock, _store, _items = _dock(qtbot, tmp_path, monkeypatch, "一")
    dock.open_settings("data")
    win = dock._settings
    qtbot.addWidget(win)
    assert str(tmp_path) in win.data_row.desc.text()
    win.backup_now()
    assert win.last_backup.is_file()
    assert str(tmp_path / "backups") in win.backup_row.desc.text()


@pytest.mark.parametrize("section", ["general", "shortcuts", "features", "data"])
def test_settings_sections_render(qtbot, tmp_path, monkeypatch, section):
    dock, _store, _items = _dock(qtbot, tmp_path, monkeypatch)
    dock.open_settings(section)
    qtbot.addWidget(dock._settings)
    assert dock._settings.current_section() == section
