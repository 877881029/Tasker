# Detail bubble attach implementation

> **For agentic workers:** TDD. Spec: `docs/superpowers/specs/2026-09-15-detail-bubble-attach-design.md`

**Goal:** Embed `DetailWindow` in `DockWindow` so chrome drag moves both.

## Tasks

- [x] RED: `test_detail_is_embedded_and_follows_dock_move`
- [x] GREEN: `detail_host` + `rail` in one `shell`; close restores right-third
- [x] `pytest tests/test_window.py tests/test_detail.py` then full suite
