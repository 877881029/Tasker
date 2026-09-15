from inspect import signature

from PySide6.QtCore import QRect

from tasker.journal import dump_journal, journal_has_text, parse_journal, prepend_record, stamp_for
from tasker.paths import attachments_dir, data_dir, db_path, tasks_dir
from tasker.shell.detail import expanded_geometry
from tasker.shell.window import geometry_for_screen
from tasker.store import STATES, Item, Store
from tasker import theme


def test_theme_tokens_are_locked():
    assert theme.PAPER == "#f4efe6"
    assert theme.CHROME == "#ebe4d8"
    assert theme.INK == "#1c1915"
    assert theme.MUTED == "#8a8176"
    assert theme.COBALT == "#2563eb"
    assert theme.COBALT_HOVER == "#1d4ed8"
    assert theme.CARD == "#fffaf2"
    assert theme.LINE == "#e4d9c7"
    assert theme.PENDING_BG == "#ecfdf3"
    assert theme.PENDING_LINE == "#bbf7d0"
    assert theme.URGENT_BG == "#fef2f2"
    assert theme.URGENT_LINE == "#fecaca"
    assert theme.DONE_BG == "#e5e7eb"
    assert theme.DONE_LINE == "#d1d5db"
    assert theme.PENDING_DOT == "#22c55e"
    assert theme.URGENT_DOT == "#ef4444"
    assert theme.DONE_DOT == "#9ca3af"
    css = theme.dock_style()
    assert "border-radius:16px" in css
    assert "text-decoration:none" in theme.card_style("pending")
    assert "line-through" not in theme.card_style("done")


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
