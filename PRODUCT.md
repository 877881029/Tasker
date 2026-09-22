# Product

<!-- impeccable:product-schema 1 -->

## Platform

windows-desktop

## Users

Tasker is primarily for its owner and other heavy desktop workers who spend long stretches at a Windows computer. They need to capture the next task quickly, keep it visible without opening a full project-management system, and append a continuous work log without breaking concentration.

## Product Purpose

Tasker is a local Windows desktop workbench for keeping active tasks and their running journals together. It succeeds when capturing, resuming, updating, and completing work requires almost no navigation or context switching.

## Positioning

Tasker behaves like a quiet paper note parked beside the work area: always available, visually restrained, and centered on the current task plus its history. Unlike a conventional task manager, it does not turn personal work into a hierarchy of projects, dashboards, accounts, or collaboration workflows.

## Operating Context

- Runs as a frameless Windows tool window with a system-tray presence.
- Stays available beside other desktop applications throughout the workday.
- Supports fast mouse use and keyboard-first journal workflows.
- Stores one readable Markdown file per task under the local Tasker data directory.
- Uses the task list for prioritization and the journal for continuity, handoff to the future self, and resuming interrupted work.

## Capabilities and Constraints

- Tasks have stable IDs and the states `pending`, `urgent`, and `done`.
- Search covers task titles and journal content.
- A task detail surface combines title, state controls, and a reverse-chronological journal.
- `Ctrl+I` begins writing, `Ctrl+S` saves while keeping the detail open, and `Esc` saves and closes the detail.
- The application remains local-first and does not require an account, cloud service, or network connection.
- Task data remains human-readable Markdown; the on-disk schema and public Store/Journal interfaces are compatibility boundaries.
- The tray lifecycle, single-instance behavior, frameless shell, desktop shortcut, and frozen Windows executable remain part of the product.

## Brand Commitments

- Product name: Tasker.
- Identity: a cobalt `T` on a paper-like Windows desktop surface.
- The interface must remain quiet, direct, and tool-like rather than becoming a conventional dashboard.
- The locked theme, geometry, object names, keyboard chords, and public interfaces are defined by `docs/superpowers/specs/2026-09-15-ui-contract-lock.md`.

## Evidence on Hand

- Current product status and validated behavior: `docs/STATUS.md`.
- Locked visual and interface contract: `docs/superpowers/specs/2026-09-15-ui-contract-lock.md`.
- Current implementation: `src/tasker/`.
- Regression coverage: `tests/`.
- Windows packaging and desktop integration: `scripts/build_windows.ps1` and `src/tasker/shell/shortcut.py`.
- No testimonials, usage analytics, benchmarks, or external customer claims are available; future work must not fabricate them.

## Product Principles

1. **Stay beside the work.** Tasker supports the primary activity instead of becoming another destination to manage.
2. **Preserve continuity.** A task and its running journal form one durable context that is easy to resume.
3. **Minimize interaction cost.** Common actions should be immediate, keyboard-friendly, and free of unnecessary navigation.
4. **Keep ownership local.** Data remains readable, portable, and usable without an account or network dependency.
5. **Refine without identity drift.** UI improvements may strengthen hierarchy, spacing, feedback, and resilience while preserving the paper metaphor and locked contracts.

## Accessibility & Inclusion

Tasker should remain fully operable with keyboard and mouse, preserve visible focus, maintain readable contrast and type, tolerate long or missing content, and respect Windows display scaling.
