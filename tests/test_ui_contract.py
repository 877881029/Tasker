from inspect import signature

from PySide6.QtCore import QRect

from tasker.journal import dump_journal, journal_has_text, parse_journal, prepend_record, stamp_for
from tasker.paths import attachments_dir, data_dir, db_path, tasks_dir
from tasker.shell.detail import expanded_geometry
from tasker.shell.window import geometry_for_screen
from tasker.store import STATES, Item, Store
from tasker import theme


def test_theme_tokens_are_locked():
    assert theme.PAPER == "#f6f2ee"
    assert theme.CHROME == "#f1ebe7"
    assert theme.HOVER == "#e9e2dd"
    assert theme.SELECTED == "#e2dad5"
    assert theme.INK == "#1f1d1a"
    assert theme.MUTED == "#6b655f"
    assert theme.COBALT == "#0969da"
    assert theme.COBALT_HOVER == "#0757b8"
    assert theme.CARD == "#fdfbf9"
    assert theme.LINE == "#e6dfda"
    assert theme.LINE_STRONG == "#d6cec8"
    assert theme.PENDING_BG == "#dafbe1"
    assert theme.PENDING_LINE == "#aceebb"
    assert theme.URGENT_BG == "#ffebe9"
    assert theme.URGENT_LINE == "#ffcecb"
    assert theme.DONE_BG == "#eaeef2"
    assert theme.DONE_LINE == "#d0d7de"
    assert theme.PENDING_DOT == "#1a7f37"
    assert theme.URGENT_DOT == "#cf222e"
    assert theme.DONE_DOT == "#8c959f"
    assert theme.UI_FAMILIES[0] == "Segoe UI"
    css = theme.dock_style()
    assert "border-radius:10px" in css
    assert "QLineEdit#search{background:transparent" in css
    assert "border-radius:8px" in css
    assert "QLineEdit#search:hover,QLineEdit#search:focus{border:none" in css
    assert "border-radius:6px" in css
    assert "QToolButton#pinBtn:checked" in css
    assert "QToolButton#addBtn:pressed" in css
    assert f"QToolButton#viewToggle:hover{{background:{theme.HOVER}" in css
    assert f"QWidget#rail{{background:{theme.CHROME}" in css
    assert f"QWidget#detailHost{{background:{theme.PAPER}" in css
    assert theme.COBALT not in css.split("QWidget#shell[bubble='true']")[1].split("}")[0]
    assert "text-decoration:none" in theme.card_style("pending")
    assert "line-through" not in theme.card_style("done")
    assert theme.SELECTED in theme.card_style("pending", selected=True)
    menu = theme.menu_style()
    assert "border-radius:8px" in menu and theme.HOVER in menu


def test_geometry_contract_locked():
    avail = QRect(0, 0, 1200, 800)
    geo = geometry_for_screen(avail)
    assert geo.width() == 400
    assert geo.x() == 800
    assert expanded_geometry(avail) == avail


def test_item_and_store_interface_locked():
    assert STATES == ("pending", "urgent", "done")
    assert Item.__dataclass_fields__.keys() == {
        "id",
        "title",
        "state",
        "status_pin",
        "body_md",
        "created_at",
        "updated_at",
        "resume_state",
        "deadline",
    }
    for name in (
        "create",
        "delete",
        "collapse_blank_drafts",
        "ensure_draft",
        "get",
        "save",
        "list_visible",
        "cycle_color",
        "set_done",
        "write_paste_png",
        "set_deadline",
    ):
        assert callable(getattr(Store, name))
    assert list(signature(Store.list_visible).parameters) == ["self", "query"]
    assert callable(stamp_for)
    assert callable(parse_journal)
    assert callable(dump_journal)
    assert callable(prepend_record)
    assert callable(journal_has_text)
    assert callable(data_dir)
    assert callable(tasks_dir)
    assert callable(attachments_dir)
    assert callable(db_path)
