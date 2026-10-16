import re
import string
from dataclasses import replace
from pathlib import Path

import pytest

from tasker import i18n
from tasker.i18n import EN, set_language, tr
from tasker.store import Store

SRC = Path(__file__).resolve().parents[1] / "src" / "tasker"


@pytest.fixture
def english():
    set_language("en")
    yield
    set_language("zh")


def _fields(template: str) -> set[str]:
    return {name for _lit, name, _spec, _conv in string.Formatter().parse(template) if name}


def test_every_translated_literal_has_english():
    missing = []
    pattern = re.compile(r'\btr\(\s*"((?:[^"\\]|\\.)*)"')
    for path in SRC.rglob("*.py"):
        for literal in pattern.findall(path.read_text(encoding="utf-8")):
            text = literal.encode().decode("unicode_escape").encode("latin-1").decode("utf-8")
            if re.search(r"[\u4e00-\u9fff]", text) and text not in EN:
                missing.append((path.name, text))
    from tasker.settings import FIXED_KEYS, SHORTCUTS
    from tasker.shell.settings_window import FEATURES, SettingsWindow
    from tasker.theme import STATE_LABEL

    data = [label for label in STATE_LABEL.values()]
    data += [text for spec in SHORTCUTS.values() for text in spec[:2]]
    data += [text for pair in FIXED_KEYS for text in pair]
    data += [text for pair in FEATURES for text in pair]
    data += [text for section in SettingsWindow.SECTIONS for text in (section[1], section[3])]
    missing += [("data", text) for text in data if re.search(r"[\u4e00-\u9fff]", text) and text not in EN]
    assert missing == []


def test_english_templates_keep_placeholders():
    bad = [zh for zh, en in EN.items() if _fields(zh) != _fields(en)]
    assert bad == []


def test_tr_switches_language(english):
    assert tr("紧急") == "Urgent"
    assert tr("已删除「{name}」", name="x") == 'Deleted "x"'
    assert tr("没有翻译的字") == "没有翻译的字"
    set_language("fr")
    assert i18n.language() == "zh" and tr("紧急") == "紧急"


def test_english_search_keywords(tmp_path):
    store = Store(tmp_path)
    urgent = store.save(replace(store.create(), title="a", state="urgent", resume_state="urgent"))
    done = store.save(replace(store.create(), title="b", state="done"))
    assert [i.id for i in store.list_visible("urgent")] == [urgent.id]
    assert [i.id for i in store.list_visible("Done")] == [done.id]


def test_dock_and_settings_render_in_english(qtbot, tmp_path, monkeypatch, english):
    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    from tasker.shell.window import DockWindow

    store = Store(tmp_path)
    item = store.save(replace(store.create(), title="t", state="urgent", resume_state="urgent"))
    dock = DockWindow(store)
    qtbot.addWidget(dock)
    assert dock.search.placeholderText() == "Search tasks or logs…"
    labels = [a.text() for a in dock.tray.contextMenu().actions() if a.text()]
    assert labels[0] == "Show" and labels[-1] == "Quit"
    assert [a.text() for a in dock.cards()[0].status_menu().actions()][:3] == ["Normal", "Urgent", "Done"]
    dock.open_detail(item.id)
    assert dock._detail.journal_status.text().startswith("Ctrl+I write")
    dock.open_settings()
    win = dock._settings
    qtbot.addWidget(win)
    assert [b.text() for b in win.nav_buttons.values()] == ["General", "Shortcuts", "Features", "Data"]
    assert win.header_title.text() == "General"


def test_language_switch_offers_restart(qtbot, tmp_path, monkeypatch):
    from tasker.settings import get_setting
    from tasker.shell.window import DockWindow

    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    store = Store(tmp_path)
    dock = DockWindow(store)
    qtbot.addWidget(dock)
    dock.open_settings()
    win = dock._settings
    qtbot.addWidget(win)
    assert win.language_buttons["zh"].isChecked()
    assert win.restart_row.isHidden()
    win.language_buttons["en"].click()
    assert get_setting(store.root, "language") == "en"
    assert not win.restart_row.isHidden()
    restarted = []
    monkeypatch.setattr(dock, "restart_app", lambda: restarted.append(1))
    win.restart()
    assert restarted
    win.language_buttons["zh"].click()
    assert win.restart_row.isHidden()


def test_settings_search_filters_rows_and_sections(qtbot, tmp_path, monkeypatch):
    from tasker.shell.window import DockWindow

    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    dock = DockWindow(Store(tmp_path))
    qtbot.addWidget(dock)
    dock.open_settings()
    win = dock._settings
    qtbot.addWidget(win)
    win.search.setText("备份")
    assert win.current_section() == "data"
    assert win.nav_buttons["general"].isHidden() and not win.nav_buttons["data"].isHidden()
    assert win.rows["auto_backup"].isVisibleTo(win.pages_by_key["data"])
    assert not win.data_row.isVisibleTo(win.pages_by_key["data"])
    win.search.setText("zzz-nothing")
    assert not win.pages.currentWidget().empty.isHidden()
    win.search.clear()
    assert all(not b.isHidden() for b in win.nav_buttons.values())
    assert win.data_row.isVisibleTo(win.pages_by_key["data"])


def test_settings_window_is_frameless_with_close(qtbot, tmp_path, monkeypatch):
    from PySide6.QtCore import Qt
    from tasker.shell.window import DockWindow

    monkeypatch.setenv("TASKER_DATA_DIR", str(tmp_path))
    dock = DockWindow(Store(tmp_path))
    qtbot.addWidget(dock)
    dock.open_settings()
    win = dock._settings
    qtbot.addWidget(win)
    assert win.windowFlags() & Qt.WindowType.FramelessWindowHint
    win.close_btn.click()
    assert not win.isVisible()
