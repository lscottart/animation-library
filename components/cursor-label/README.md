# Cursor label

<img src="../../media/cursor-label.gif" alt="Cursor label: (View project) across a grid." width="100%">

A word like "(View)" rolls into a one-line window at the cursor over anything marked `data-cursor-label`, trails the pointer on a soft lag, and rolls out when it leaves. One component for every target; white with a difference blend, so it reads on photos and on paper.

## With Claude Code

```
/animations:cursor-label the project grid: (View project)
```

The skill is [`skills/cursor-label.md`](../../skills/cursor-label.md). It checks your project first, writes these files where your project keeps components, uses the component where you ask, and runs its own checks.

## Without it

| File | Where it goes |
|---|---|
| `CursorLabel.tsx` | `components/ui/` (or `src/components/ui/`), mounted once in the layout |

Needs: `gsap`.

The skill file explains the rest: the props, the values and why they were chosen, and the ways it breaks.

## Tested

`cursor_extra.py` in [`tests/`](../../tests/), on three fresh projects (App Router with Tailwind v4 and v3, Pages Router without Tailwind), in dev and production, in Chromium, Firefox and WebKit.
