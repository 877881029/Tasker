# Tasker Freeze Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One setup.ps1 install freezes `dist\Tasker\Tasker.exe` with the cobalt T icon.

**Architecture:** Keep freeze in `build_windows.ps1`. setup.ps1 calls it after pip. Launch frozen exe by default.

**Tech Stack:** PyInstaller onedir, PowerShell, existing PySide6 WebEngine.

## Global Constraints

- Do not commit `dist/` or `build/`.
- No Docker, no Vikunja, no Node web bundles.
- User asked to keep developing without extra gates.

---

### Task 1: Spec, packaging tests, freeze scripts

- [x] Failing packaging/setup tests then GREEN `tasker.spec`, `build_windows.ps1`, setup `-SkipBuild`, frozen shortcut target
- [x] Full pytest; run freeze; STATUS; push `origin/main`
