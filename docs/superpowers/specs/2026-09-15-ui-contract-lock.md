# Tasker UI contract (locked theme + interfaces)

Date: 2026-09-15  
Status: **Locked.** Layout polish is allowed. Theme tokens and the interfaces below are **not**.  
Progress ledger: `docs/STATUS.md`

This is the snapshot of the shipping UI so someone else can refine spacing, type scale, or widget arrangement **without changing the product identity or the code that other modules call**.

If a change needs a new color, a new `Store` method, a new keyboard chord, or a new on-disk shape, stop and get a new spec. Do not “just tweak” `theme.py` or the signatures in §3.

---

## 1. What you may change

- Padding, gaps, font sizes **that are not named tokens**, control sizes, scroll behavior, empty-state copy, alignment, and visual hierarchy **as long as** you keep using the locked colors, radii, and object names.
- Internal helpers (`_foo`) that are not listed in §3.

## 2. Theme — locked

Source of truth: `src/tasker/theme.py`. Do not rename tokens. Do not change hex values. Do not add a second palette.

| Token | Value | Use |
|---|---|---|
| `PAPER` | `#f4efe6` | Shell, list, detail, journal background |
| `CHROME` | `#ebe4d8` | Hover plates on + / pin / × |
| `INK` | `#1c1915` | Primary text |
| `MUTED` | `#8a8176` | Secondary text, older stamps |
| `COBALT` | `#2563eb` | Accents, focus ring, bubble outline, selected card, newest stamp |
| `COBALT_HOVER` | `#1d4ed8` | Hover cobalt (reserved) |
| `CARD` | `#fffaf2` | Document code/pre fill |
| `LINE` | `#e4d9c7` | Default 1px borders, search idle |
| `PENDING_BG` / `PENDING_LINE` | `#ecfdf3` / `#bbf7d0` | Pending note |
| `URGENT_BG` / `URGENT_LINE` | `#fef2f2` / `#fecaca` | Urgent note |
| `DONE_BG` / `DONE_LINE` | `#e5e7eb` / `#d1d5db` | Done note |
| `PENDING_DOT` | `#22c55e` | Pending importance |
| `URGENT_DOT` | `#ef4444` | Urgent importance |
| `DONE_DOT` | `#9ca3af` | Done importance |

Locked geometry / chrome (not hex, still frozen):

- Shell corner radius **16px**; card radius **8px**.
- Collapsed dock = right **1/3** of available screen (`geometry_for_screen`), min width 320.
- Open detail = same window, left pane + rail; rail width stays that third; shell `bubble='true'` → **2px cobalt** outline.
- Icon: cobalt **T** `assets/icons/tasker.ico` / `tasker-t.svg`. Do not swap letter, hue, or use a screenshot of the live window as the glyph.
- Typeface for rendered HTML: Candara, Calibri, Segoe UI (see `document_style`).
- Object names used by QSS stay: `dock`, `shell`, `detailHost`, `rail`, `itemCard`, `listHost`, `listScroll`, `search`, `addBtn`, `pinBtn`, `closeDock`, `titleField`.

`card_style(state)` must keep mapping `pending|urgent|done` → those fills and **no strikethrough**.

---

## 3. Interfaces — locked

### 3.1 Data on disk

- Root: `TASKER_DATA_DIR` or `%LOCALAPPDATA%\Tasker\`.
- Tasks: `tasks/<stable-id>.md`. Filename does not follow the title.
- YAML keys (required): `title`, `state`, `resume_state`, `created_at`, `updated_at`.
- `state`: only `pending` | `urgent` | `done`.
- Body under YAML: reverse-chronological journal via `dump_journal` / `parse_journal`. Stamp `YYMMDD.hAM/PM`. Adjacent records separated by one blank line. `Ctrl+I` always **prepends** a new record (same hour ≠ merge) **and makes the whole journal editor writable**.
- Image/link paths in Markdown are not rewritten. Delete unlinks the `.md` only.
- Clipboard-only PNG may be written under `tasks/<id>/`.

### 3.2 `tasker.paths`

```
data_dir() -> Path
tasks_dir() -> Path          # data_dir() / "tasks"
attachments_dir(item_id) -> Path   # tasks_dir() / item_id
db_path() -> Path            # migrate-only leftover
```

### 3.3 `tasker.journal`

```
stamp_for(when: datetime) -> str
parse_journal(body: str) -> list[tuple[str, str]]
dump_journal(entries: list[tuple[str, str]]) -> str
prepend_record(entries, when) -> list[tuple[str, str]]
journal_has_text(body: str) -> bool
```

JSON journal lists remain readable for one-shot sqlite migrate.

### 3.4 `tasker.store`

```
STATES = ("pending", "urgent", "done")

@dataclass(frozen=True)
class Item:
    id, title, state, status_pin, body_md, created_at, updated_at, resume_state

is_empty_note(item) -> bool
is_blank_draft(item) -> bool

class Store:
    def __init__(self, root: Path | None = None) -> None
    def create(self) -> Item
    def delete(self, item_id: str) -> None
    def collapse_blank_drafts(self) -> Item | None
    def ensure_draft(self) -> Item
    def get(self, item_id: str) -> Item | None
    def save(self, item: Item) -> Item
    def list_visible(self, query: str = "") -> list[Item]
    def cycle_color(self, item_id: str) -> Item   # pending ↔ urgent; done unchanged
    def set_done(self, item_id: str, done: bool) -> Item
    def write_paste_png(self, item_id: str, data: bytes) -> Path
```

List order locked: urgent, then pending, then done; within a group newest `updated_at` first. Search casefolds title + body.

### 3.5 Shell widgets

**`DockWindow`**

- Flags: `Qt.Tool | FramelessWindowHint` (+ `WindowStaysOnTopHint` when pinned). No taskbar app button.
- Tray: `QSystemTrayIcon`; Trigger/DoubleClick or menu 「显示」 → `show_from_tray`; 「退出」 quits. Dock × **hides** (process stays).
- Chrome left-to-right: search (stretch), `+`, pin, ×. No 「事项」 label.
- `+` → `ensure_draft` then `open_detail`. Card click → `open_detail`. Search filters `list_visible`.
- Public: `refresh()`, `open_detail(item_id: str)`, `show_from_tray()`, `tray`.
- `geometry_for_screen(avail: QRect) -> QRect` stays right-third.

**`DetailWindow`**

- Embedded in `detail_host` (not a second `Qt.Tool` window when parented).
- Header: importance 32px dot, title, 完成, 删除. **No** 保存 / 关闭 buttons.
- Journal open = read-only. `Ctrl+I` → `begin_write` (prepend a new record and make the **whole** editor writable). `Ctrl+S` → `save_keep_open` (write file, stay open, read-only). `Esc` → `close_detail` (save + hide bubble).
- Title / dot / done write YAML immediately.
- Public: `load(item)`, `begin_write()`, `save_keep_open()`, `save_all()`, `close_detail()`, `delete_item()`, signal `closed`.
- `expanded_geometry(avail) -> QRect` fills available screen.

**`JournalPane`**

- One wrapped editor plus a 118px timestamp gutter (stamps are not duplicated in the body). Not one widget per record.
- `load(body)`, `collect() -> str`, `latest_status() -> str`, `begin_write(when=None)`, `set_all_readonly()`, `head_edit()`.

### 3.6 App / IPC

- `TaskerApp.store`, `TaskerApp.dock`, `show_dock()`.
- `main`: `setQuitOnLastWindowClosed(False)`; desktop shortcut overwrite to frozen exe when present.
- Single instance: `Tasker.SingleInstance.v1` (`server_name()`). Second launch activates existing dock.
- `APP_USER_MODEL_ID = "AgentDevelopor.Tasker"`.

---

## 4. Current UI map (for polishers)

```
[ system tray T ]
        |
        v
┌──────────────────────── shell (paper, 16px) ─────────────────────────┐
│ [detailHost: journal + header] │ notch │ [rail: search + + pin ×]   │
│                                 │       │  [scroll of ItemCards]      │
└─────────────────────────────────┴───────┴────────────────────────────┘
```

Collapsed: only `rail`, right third. Expanded: full available geometry, cobalt 2px bubble border, selected card cobalt 2px.

Cards: solid 20px state dot + wrapping title only (no inline 详情 / 完成).

---

## 5. Enforcement

- Cursor rule: `.cursor/rules/ui-theme-interface-lock.mdc`
- Tests: `tests/test_ui_contract.py` (token hex + `Item` fields + `Store` methods + geometry).
- Changing this file requires an explicit user-approved spec, not a drive-by UI PR.
