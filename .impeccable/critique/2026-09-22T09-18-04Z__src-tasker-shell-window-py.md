---
target: Tasker native desktop shell
total_score: 15
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 3
timestamp: 2026-09-22T09-18-04Z
slug: src-tasker-shell-window-py
---
Method: dual-agent (A: 12afd8c6-8290-4730-8dc4-19b1fa12e01f · B: f5a46273-688c-4035-8918-fc7507038351)

# Tasker Native UI Critique

## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 1 | Editing, saving, filtering, and tray lifecycle are mostly silent |
| 2 | Match System / Real World | 3 | The paper-and-journal metaphor is strong and specific |
| 3 | User Control and Freedom | 1 | Delete is immediate; close/hide semantics are unclear |
| 4 | Consistency and Standards | 3 | Palette and layout are coherent; focus and native/Chromium cues diverge |
| 5 | Error Prevention | 0 | Irreversible deletion and silent mode transitions |
| 6 | Recognition Rather Than Recall | 1 | The primary journal workflow requires memorized shortcuts |
| 7 | Flexibility and Efficiency | 2 | Efficient after learning, but mouse and keyboard paths are asymmetric |
| 8 | Aesthetic and Minimalist Design | 3 | Calm and focused, but some blank states lose hierarchy |
| 9 | Error Recovery | 0 | No visible error, undo, or recovery surface |
| 10 | Help and Documentation | 1 | Tooltips exist, but primary workflow guidance does not |
| **Total** | | **15/40** | **Poor** |

## Design Specificity Verdict

Tasker is strongly authored for its product: warm paper, opaque ink, disciplined cobalt, stable rail geometry, local Markdown, and one task plus one journal form a coherent “桌边工作纸” world. The weakness is not visual identity but operational legibility. Critical modes, shortcuts, task-state meanings, save completion, empty results, destructive consequences, and recovery are hidden or communicated only by color.

The deterministic detector returned one advisory at `src/tasker/shell/window.py:228`: `border-radius: 10px` is outside the DESIGN.md scale. This is a false positive caused by scanning an embedded Qt stylesheet as web CSS; the value creates a circular 20px state dot and is semantically correct. Native browser overlays were unavailable because Tasker is a PySide6/Qt QWidget application rather than a DOM surface.

## Overall Impression

The product already looks distinct and restrained, but “quiet” has drifted into “silent.” The single biggest opportunity is to make state and next actions legible without adding buttons, chrome, colors, or dashboard structure.

## What's Working

1. The paper, ink, cobalt, and humanist type system gives Tasker a specific desktop-tool identity.
2. One rail, one current task, and one continuous journal keep cognitive structure unusually clean.
3. Stable rail placement, readable Markdown storage, and stable read/write typography support interruption-heavy work.

## Priority Issues

### P1 — Irreversible deletion lacks prevention or recovery
- **Why it matters:** One click permanently unlinks the task Markdown file beside the routine completion control.
- **Fix:** Add a compact two-step inline confirmation in the existing header without changing Store APIs or introducing a modal.
- **Suggested command:** `/impeccable clarify`

### P1 — Core journal workflow and save state are undiscoverable
- **Why it matters:** A first-time user can reasonably conclude the journal is permanently read-only, and Ctrl+S gives no reassurance.
- **Fix:** Add contextual muted shortcut guidance, an existing-token write-mode cue, and a brief saved/read-only acknowledgement without adding buttons.
- **Suggested command:** `/impeccable polish`

### P1 — Cards and state are not keyboard/assistive operable
- **Why it matters:** `ItemCard` is mouse-only; task state is color-only; tools lack explicit accessible names and consistent focus treatment.
- **Fix:** Make cards focusable and Enter/Space activatable, provide accessible title/state descriptions, add visible cobalt focus, and define tab order.
- **Suggested command:** `/impeccable audit`

### P2 — Empty and lifecycle states are indistinguishable
- **Why it matters:** No tasks, no search matches, and an empty journal all resemble blank or failed rendering; × says close while it hides to tray.
- **Fix:** Add distinct muted empty-state copy and change the tooltip to “隐藏到托盘.”
- **Suggested command:** `/impeccable clarify`

### P2 — Expanded content lacks an intentional reading measure
- **Why it matters:** The window may be wide by design, but short journal content leaves an undifferentiated field and weak header-to-body hierarchy.
- **Fix:** Improve internal alignment, spacing, and empty-journal anchoring while preserving all locked outer geometry.
- **Suggested command:** `/impeccable layout`

## Persona Red Flags

- **Alex, power user:** Cannot reliably tab to or open task cards from the keyboard.
- **Jordan, first-time user:** Receives no visible invitation to use Ctrl+I and may believe the journal is read-only.
- **Sam, accessibility-dependent user:** State is color-only, focus is incomplete, no accessible names are assigned, and MUTED on PAPER is low for small text.
- **Riley, stress tester:** Silent saves and immediate deletion undermine confidence after interruption.
- **Heavy desktop worker:** Stable rail and tray fit the workflow, but the expanded paper needs stronger internal structure to remain supportive rather than vacant.

## Minor Observations

- `PRODUCT.md` must describe the native Windows reality even though Impeccable's platform enum lacks a Windows value.
- Delete uses hard-coded `#b91c1c`, outside the locked token set.
- Search has an explicit focus border; tools, cards, title, checkbox, and delete do not have an equivalent focus system.
- No dedicated tests cover tab traversal, accessible names, empty states, focus visibility, or Windows scale factors.

## Questions to Consider

1. Is quiet being mistaken for silent when the system needs to confirm mode and persistence?
2. If journaling cannot be discovered without documentation, is it truly the primary capability?
3. Why is deletion optimized to one click while writing requires memorized chords?
4. Can blank paper feel intentional without becoming visually busy?
