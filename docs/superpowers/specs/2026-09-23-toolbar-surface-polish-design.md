# Toolbar surface polish design

Date: 2026-09-23  
Status: Approved by user feedback

## Goal

Remove the default-widget and hand-assembled feel from Tasker's first row while
preserving every existing action, shortcut, object name, theme token, window
behavior, and public interface.

## Problem

The current row mixes a 4px transparent system-like search field with three bare
32px tool glyphs. The shell has a soft 16px paper silhouette and cards use an 8px
radius, so the toolbar reads as a separate unfinished implementation rather than
part of the same product.

The search focus state is especially weak: it resembles a stock Windows input
with a blue underline. Tool controls have no visible surface until hover, uneven
glyph weights, and insufficient visual grouping.

## Visual direction

Treat the first row as one quiet control composition:

- Search is an inset light-paper well using existing `CARD`, `LINE`, `INK`, and
  `MUTED` tokens.
- Search radius is 12px, height is 38px, and horizontal padding is 12px.
- Search focus uses a complete 2px cobalt ring without changing geometry.
- Add, pin, and hide use matching 36px rounded-square paper controls.
- Tool controls use 10px radius, `CARD` fill, and a `LINE` hairline at rest.
- Hover/checked use `CHROME`; focus uses a 2px cobalt ring; pressed uses
  `CHROME` with cobalt-hover text where applicable.
- The top row uses 14px outer spacing and 8px internal gaps.
- Placeholder text is explicitly `MUTED`, avoiding platform-default gray.

This is surface refinement, not elevation. No shadows, gradients, blur, glass,
new palette, animation, or permanent toolbar band are introduced.

## Behavior and contract

Unchanged:

- Search filtering and placeholder copy.
- Add, pin, and hide actions.
- Tab order and accessible names.
- `Ctrl+I`, `Ctrl+S`, and `Esc`.
- Tray lifecycle, Store/Journal APIs, Markdown, geometry, drag/resize, and shell
  and card radii.
- Locked token values and existing public object names.

Allowed internal changes:

- Control dimensions, padding, margins, QSS state selectors, placeholder palette,
  and private style helpers.

## Acceptance criteria

1. Search has a full rounded outline at rest and focus, with no stock blue
   underline.
2. The three tools have equal 36px hit targets and matching rounded paper plates.
3. Pin checked, hover, keyboard focus, and pressed states remain distinct.
4. Top-row controls align vertically and preserve the existing left-to-right tab
   order.
5. The row remains usable at 125%, 150%, and 200% Windows display scaling.
6. Existing UI contract and full test suite pass.

