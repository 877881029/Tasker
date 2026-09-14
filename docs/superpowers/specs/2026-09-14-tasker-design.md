# Tasker 本地工作台设计

Date: 2026-09-14  
Status: Approved by user (layout A+; PySide6 + SQLite; details reuse Reader Markdown)  
Progress ledger: `docs/STATUS.md`

## 1. Goal

**Tasker** is a local Windows desktop workbench for the user's current work. It shows every item in a right-hand dock (about one third of the screen), with a searchable list, a done flag, and a detail pane for title, pinned latest status, Markdown body, hyperlinks, and pasted screenshots.

It runs like Reader: double-click a local app, no Docker, no hosted Vikunja process. Vikunja is a reference for the task/project idea only, not a dependency.

Later Tasker may be embedded into Reader. First ship is a sibling repo with the same agent-handoff git rhythm as Reader.

## 2. Product surface

### 2.1 Window

- Docked to the **right edge**, width **≈ 1/3 of the screen** (not a thin strip).
- Paper chrome aligned with Reader: paper `#f4efe6`, chrome `#ebe4d8`, cobalt `#2563eb`.
- Title-bar **pin**: pinned = always-on-top; unpinned = normal z-order.
- Clicking an item opens **detail on the left** (over the remaining desktop area), not a second column inside the dock.

### 2.2 Icon

Same family as Reader’s blue **R**: a **transparent** square, one **uppercase letter** drawn with rounded cobalt strokes, not a filled badge or a different hue.

- Letter: **T** (Tasker).
- Stroke color: Reader cobalt `#2563EB` (same as `assets/icons/reader-r.svg`).
- Construction: transparent 256×256 field; stroke-width 34; `stroke-linecap` / `stroke-linejoin` round — match Reader’s ribbon-R, not a serif print T and not a boxed tile.
- Master: `assets/icons/tasker-t.svg`. Raster: PNG 16 / 24 / 32 / 48 / 256 plus multi-size `assets/icons/tasker.ico`.
- Use `tasker.ico` for the window icon, taskbar, desktop shortcut, and later frozen `Tasker.exe` `--icon`. Do not snapshot the live window as the taskbar glyph.

### 2.2 Dock (right)

Top row, left to right: **事项** label, **search field**, **`+`**, **pin**.

- **`+`**: create an empty pending item and focus the title for inline edit.
- **Search**: filter the list to **matching items only** (title and body). Non-matches are omitted, not dimmed in place.
- Each card has a **left color bar**. Click cycles **pending (green) ↔ urgent (red)** only.
- **Done** is a separate checkbox. Done cards use a **gray background**. Text stays readable. **No strikethrough.**
- No progress bar, no multi-column kanban, no Gantt, no assignees.

Default list order: urgent first, then pending, then done; within a group, newest-updated first. Search results keep that order among matches.

### 2.3 Detail (left)

- Editable **title** (same string as the dock card).
- **Pinned latest-status** field at the top of the pane, always above the body.
- Body uses **Reader's Markdown visual + edit path** (WebEngine visual preview and an edit mode).
- **Paste image**: write a file under the Tasker data directory, insert a Markdown image pointing at that file.
- **Hyperlinks**: Markdown links are clickable in visual mode; pasting a URL becomes a link.
- No comment thread, no members, no attachments UI beyond paste-into-body.

## 3. Architecture

| Piece | Choice |
|---|---|
| Repo | `C:\Research\AgentDevelopor\Tasker` (sibling of Reader), package `tasker` |
| UI | PySide6, Reader-like window shell and theme tokens |
| Store | SQLite under `%LOCALAPPDATA%\Tasker\` (tests use `TASKER_DATA_DIR`) |
| Body | Markdown on disk/db + Reader-style `MarkdownVisualView` / text edit |
| Images | Files in `%LOCALAPPDATA%\Tasker\attachments\<item-id>\` |
| Icons | `assets/icons/tasker-t.svg` + generated PNG/`tasker.ico` (Reader pipeline) |
| Not in v1 | Vikunja binary, HTTP server for others, accounts, Docker, Office/PPTX/PDF |

Main window owns the dock list and search. Selecting an id opens a detail widget that loads Markdown for that item. Saving writes SQLite + attachment files. Pin only toggles `WindowStaysOnTopHint`.

Data model (logical):

- `items.id` (stable)
- `items.title`
- `items.state`: `pending` | `urgent` | `done`
- `items.status_pin` (plain text, the pinned latest status)
- `items.body_md` (Markdown)
- `items.created_at`, `items.updated_at`

No separate project table in v1: one flat list is the workbench.

## 4. Non-goals (v1)

- Progress percentages, swimlanes, due dates, recurrence, tags, CalDAV.
- Running or bundling Vikunja.
- Multi-user sync or a browser-only deploy.
- Embedding into Reader (documented as a later step).
- Frozen `Tasker.exe` in the first implementation slice (source `setup.ps1` first, freeze when the list+detail loop works).

## 5. Testing

- New item via `+` appears as `pending` with empty title focused.
- Color-bar click: `pending` → `urgent` → `pending`; does not mark done.
- Checking done sets `done` and gray style. Remember the last non-done state (`pending` or `urgent`); unchecking restores that state, not always `pending`.
- Search `"PDF"` hides non-matching rows; clearing search restores the full list including done items.
- Done items are not struck through.
- Pin on: window stays on top; pin off: it does not.
- Detail: edit title persists to the card; `status_pin` stays above body after reload.
- Paste image: a file exists under attachments and `body_md` contains an image reference to it.
- Markdown visual opens links without leaving the app for `http(s)` (external browser or in-pane policy: **open in the system browser**; do not fetch remote images in the visual preview).
- Tests must not write to the real `%LOCALAPPDATA%\Tasker` (always `TASKER_DATA_DIR`).
- Icon assets exist (`tasker-t.svg`, size PNGs, `tasker.ico`). Corner pixels are transparent; a stroke sample is cobalt `#2563EB` (blue channel dominant, same checks as Reader `tests/test_icon_assets.py`). Window and shortcut load `tasker.ico`, not `reader.ico`.

## 6. Handoff and deploy

Same loop as Reader:

1. Spec in `docs/superpowers/specs/`
2. Plan in `docs/superpowers/plans/`
3. `docs/STATUS.md` is the live ledger
4. Commit and push `origin/main` at spec / plan / task / session boundaries
5. `scripts/setup.ps1` (implementation): venv, install, launch `python -m tasker`
6. Clone-and-run is the colleague path; no Docker Compose

## 7. Decisions already made

- Layout A+ (right 1/3 dock, left detail, search beside 事项, done = gray fill only).
- New empty card from dock `+` only (search Enter does not create).
- Urgent via color bar; done via checkbox.
- Pin control for always-on-top.
- Details reuse Reader Markdown stack, with paste image + hyperlinks required.
- Working title of the product: **Tasker**.
- App icon is a same-series cobalt rounded **T** on a transparent field (`#2563EB`), parallel to Reader’s **R**.
