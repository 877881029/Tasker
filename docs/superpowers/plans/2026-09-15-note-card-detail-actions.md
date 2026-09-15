# Note Card and Detail Actions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline in this session).

**Goal:** Taller note cards with a solid importance dot and title only; detail owns done and delete.

**Architecture:** `ItemCard` drops 详情/完成; `TitleField` opens detail on first click; `DetailWindow` adds done + delete wired to existing `Store.set_done` / `Store.delete`.

**Tech Stack:** PySide6, Tasker theme tokens, pytest-qt.

## Global Constraints

- Paper dock chrome; no 详情 button; delete does not save afterwards.
- Work on `main`; do not commit `dist/` or `build/`.

---
