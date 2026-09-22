---
name: Tasker
description: A quiet sheet of working paper parked beside the desktop.
colors:
  paper: "#f4efe6"
  chrome: "#ebe4d8"
  ink: "#1c1915"
  muted-ink: "#8a8176"
  cobalt: "#2563eb"
  cobalt-hover: "#1d4ed8"
  code-paper: "#fffaf2"
  hairline: "#e4d9c7"
  pending-paper: "#ecfdf3"
  pending-line: "#bbf7d0"
  urgent-paper: "#fef2f2"
  urgent-line: "#fecaca"
  done-paper: "#e5e7eb"
  done-line: "#d1d5db"
  pending-dot: "#22c55e"
  urgent-dot: "#ef4444"
  done-dot: "#9ca3af"
typography:
  title:
    fontFamily: "Candara, Calibri, Segoe UI, sans-serif"
    fontSize: "16pt"
    fontWeight: 400
    lineHeight: 1.25
  body:
    fontFamily: "Candara, Calibri, Segoe UI, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.72
  card:
    fontFamily: "Candara, Calibri, Segoe UI, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.4
  stamp:
    fontFamily: "Candara, Calibri, Segoe UI, sans-serif"
    fontSize: "13px"
    fontWeight: 600
    lineHeight: 1.72
rounded:
  control: "4px"
  card: "8px"
  shell: "16px"
spacing:
  xs: "4px"
  sm: "8px"
  control-gap: "10px"
  surface: "12px"
  shell: "16px"
  content: "24px"
  reading-edge: "28px"
  reading-tail: "48px"
components:
  search-field:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    typography: "{typography.card}"
    rounded: "{rounded.control}"
    padding: "4px 8px"
    height: "32px"
  tool-button:
    backgroundColor: "transparent"
    textColor: "{colors.cobalt}"
    rounded: "{rounded.control}"
    padding: "4px 8px"
    size: "32px"
  task-card:
    backgroundColor: "{colors.pending-paper}"
    textColor: "{colors.ink}"
    typography: "{typography.card}"
    rounded: "{rounded.card}"
    padding: "12px 14px"
    height: "88px"
  journal-body:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    padding: "8px 20px 32px 12px"
---

# Design System: Tasker

## Overview

**Creative North Star: "桌边工作纸"**

Tasker should feel like a warm sheet of working paper kept beside the monitor: immediately available, easy to scan, and calm enough to remain present throughout the day. Its identity comes from quiet paper, dark ink, one disciplined cobalt accent, and small state marks rather than from application chrome.

The interface is warm, restrained, and clear. It rejects dashboard density, glass effects, ornamental motion, and decorative surfaces that compete with the user's actual work. Refinement should improve rhythm, hierarchy, focus, and feedback without making Tasker feel like a project-management suite.

**Key Characteristics:**
- Warm paper and opaque ink instead of white software panels.
- Flat surfaces separated by spacing, fine lines, and state color.
- A single cobalt interaction voice used for focus, selection, and the newest journal stamp.
- Compact controls around a generous reading and writing surface.
- Native Windows behavior with minimal visible chrome.

## Colors

The palette combines warm paper neutrals with one cool cobalt accent and quiet task-state tints.

### Primary
- **Working Cobalt**: The sole interaction accent for focus, selection, links, the open-detail outline, and the newest timestamp.
- **Deep Cobalt**: Reserved for hover or pressed emphasis where the interaction needs a stronger response.

### Neutral
- **Warm Paper**: The continuous shell, rail, detail, editor, and reader surface.
- **Paper Chrome**: A subtle hover plate behind compact tools; it must never become a permanent toolbar band.
- **Opaque Ink**: Primary titles, journal text, and control copy.
- **Quiet Ink**: Secondary timestamps, placeholders, and intentionally de-emphasized text.
- **Paper Hairline**: Default input and shell borders.
- **Code Paper**: The slightly lighter inset used behind code and preformatted content.

### State Colors
- **Pending**: A pale green paper, soft green line, and solid green dot.
- **Urgent**: A pale red paper, soft red line, and solid red dot.
- **Done**: A cool gray paper, gray line, and gray dot without strikethrough.

**The One Blue Voice Rule.** Cobalt means interaction, focus, selection, or recency. Do not use it as broad decoration.

**The State Tint Rule.** Task state colors belong to cards and state dots; they do not recolor the shell, journal, or controls.

## Typography

**Display Font:** Candara with Calibri and Segoe UI fallbacks  
**Body Font:** Candara with Calibri and Segoe UI fallbacks  

**Character:** Humanist and readable rather than corporate or technical. A single family keeps the compact shell and long-form journal related while size, weight, color, and spacing provide hierarchy.

### Hierarchy
- **Title** (regular, 16pt, 1.25): Editable task title in the detail header.
- **Body** (regular, 16px, 1.72): Journal reading and writing; prioritize sustained readability.
- **Card** (regular, 15px, 1.4): Wrapping task titles in the rail.
- **Stamp** (demibold, 13px, 1.72): Right-aligned timestamps; cobalt only for the newest record.
- **Tool label** (semibold, 18px glyph scale): Compact add, pin, and close actions.

**The Reading Surface Rule.** Journal reading and writing use the same family, ink, 16px scale, and 1.72 line height so mode changes do not shift perceived typography.

## Layout

The collapsed shell occupies the right third of the available work area with a 320px minimum. Opening a task keeps the rail parked and grows the same shell leftward; the detail receives the additional width while the rail preserves its previous width.

The rail uses a compact control row followed by a top-aligned vertical card list. Controls use a 32px footprint, 8px gaps, and 12px edge spacing. Cards use 12px vertical and 14px horizontal internal padding with a 10px gap between the state dot and title.

The detail is a generous paper field. Its header groups the state dot and title as the primary cluster; completion and deletion remain secondary actions. The journal uses a fixed 118px timestamp gutter or a 7.75rem grid column, followed by a flexible text column. Long text wraps only inside the text column.

When the shell fills the available work area, its outer radius becomes zero and the paper meets the work-area edges. Otherwise the entire shell uses the full 16px paper silhouette.

**The Parked Rail Rule.** Opening, closing, or resizing detail must not make the rail jump away from its current desktop position.

**The Paper Breathing Rule.** Increase hierarchy through alignment and whitespace before introducing another border, color, or control.

## Elevation & Depth

Tasker is flat by default. It does not use drop shadows to separate content. Fine borders, tonal state papers, spacing, and the cobalt focus/selection outline carry depth and interaction state.

**The Flat Paper Rule.** Do not add glass, blur, gradients, ambient shadows, or floating-card stacks. If an interaction is unclear, repair its spacing, border, focus, or state feedback first.

## Shapes

The outer paper shell uses a soft 16px radius while inset cards use an 8px radius and compact controls use a 4px radius. State dots are fully circular. The hierarchy is deliberate: shell, content card, control.

The shell radius disappears only when the window is flush with the Windows work area. Card and control radii do not change with window size.

## Components

### Tool Buttons
- **Shape:** Compact rounded square footprint (32px with 4px hover plate).
- **Default:** Transparent paper with cobalt icon or glyph.
- **Hover / Checked:** Paper Chrome plate; no shadow or movement.
- **Focus:** A visible cobalt keyboard focus treatment must remain available.

### Search Field
- **Shape:** Restrained rounded rectangle (4px).
- **Default:** Transparent fill, Paper Hairline border, Opaque Ink.
- **Focus:** Hairline changes to Working Cobalt without changing geometry.
- **Copy:** Short placeholder, currently `查找…`.

### Task Cards
- **Shape:** Gently rounded paper card (8px), minimum 88px tall.
- **Background:** State-specific pale paper with matching soft border.
- **Content:** One solid 20px state dot and a wrapping title; no inline action clutter.
- **Hover:** Cobalt border; selected card receives the stronger 2px cobalt outline.

### Detail Header
- **Structure:** 32px state dot, flexible title field, completion control, destructive action.
- **Hierarchy:** State and title lead. Completion is secondary. Delete remains quiet red text and must not visually compete with the task.
- **Behavior:** Title and state changes persist immediately; journal save behavior remains keyboard-driven.

### Journal
- **Read mode:** Chromium-rendered paper with a fixed timestamp column and flexible Markdown text.
- **Write mode:** One wrapped editor with the same body typography and a painted timestamp gutter.
- **Recency:** Only the newest timestamp uses cobalt.
- **Empty write:** A prepended record without text disappears on save or close.

### Paper Shell
- **Collapsed:** Rail only, parked at the right third on first launch.
- **Expanded:** Detail, narrow paper notch, and the parked rail in one continuous shell.
- **Interaction:** Empty paper drags the shell; an 8px native frame supports all edge and corner resizing.

## Do's and Don'ts

### Do:
- **Do** preserve the continuous Warm Paper surface across shell, detail, editor, and reader.
- **Do** use spacing, alignment, and type hierarchy before adding visual decoration.
- **Do** keep cobalt rare and meaningful.
- **Do** test long titles, long journal lines, empty states, keyboard focus, and Windows display scaling.
- **Do** keep read and write typography visually stable.

### Don't:
- **Don't** introduce dashboard panels, navigation sidebars, analytics, project hierarchy, or collaboration chrome.
- **Don't** add glass effects, gradients, ornamental animation, or permanent shadows.
- **Don't** create a second palette or change the locked token values.
- **Don't** add inline actions to task cards or visible Save/Close buttons to the detail.
- **Don't** change the Store/Journal interfaces, Markdown schema, keyboard chords, object names, or tray lifecycle as part of visual polish.
