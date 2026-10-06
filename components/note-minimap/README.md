# Note minimap

<img src="../../media/note-minimap.gif" alt="Note minimap: Reading down a note, then a click back to The plan." width="100%">

A vertical rail of section cards (thumbnail and title) at the page edge that follows your reading on a soft, underdamped spring, with a viewfinder on the current section. Click a card to glide there. It sleeps when nothing moves.

## With Claude Code

```
/animations:note-minimap the case-study pages in app/work/[slug]/page.tsx
```

The skill is [`skills/note-minimap.md`](../../skills/note-minimap.md). It checks your project first, writes these files where your project keeps components, uses the component where you ask, and runs its own checks.

## Without it

| File | Where it goes |
|---|---|
| `NoteMinimap.tsx` | `components/ui/` (or `src/components/ui/`) |
| `NoteMinimap.css` | `components/ui/` (or `src/components/ui/`); in the Pages Router, import it in `pages/_app.tsx` |

Needs: Nothing.

The skill file explains the rest: the props, the values and why they were chosen, and the ways it breaks.

## Tested

`minimap_extra.py` in [`tests/`](../../tests/), on three fresh projects (App Router with Tailwind v4 and v3, Pages Router without Tailwind), in dev and production, in Chromium, Firefox and WebKit.
