# Focus dim

<img src="../../media/focus-dim.gif" alt="Focus dim: Four houses." width="100%">

Hover or keyboard-focus one item in a group and its siblings step back to a quarter opacity and grey. The group never flashes when the pointer crosses the gap between two items. Pure CSS with `:has()`, a Server Component, no JavaScript.

## With Claude Code

```
/animations:focus-dim the project grid on the home page
```

The skill is [`skills/focus-dim.md`](../../skills/focus-dim.md). It checks your project first, writes these files where your project keeps components, uses the component where you ask, and runs its own checks.

## Without it

| File | Where it goes |
|---|---|
| `FocusDim.tsx` | `components/ui/` (or `src/components/ui/`) |
| `FocusDim.css` | `components/ui/` (or `src/components/ui/`); in the Pages Router, import it in `pages/_app.tsx` |

Needs: Nothing. `:has()` needs Chrome 105, Safari 15.4 or Firefox 121.

The skill file explains the rest: the props, the values and why they were chosen, and the ways it breaks.

## Tested

`focusdim_extra.py` in [`tests/`](../../tests/), on three fresh projects (App Router with Tailwind v4 and v3, Pages Router without Tailwind), in dev and production, in Chromium, Firefox and WebKit.
