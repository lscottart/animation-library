# List hover sliding fill

<img src="../../media/list-hover-sliding-fill.gif" alt="List hover sliding fill: The house index." width="100%">

A link list whose hover fill slides from row to row like one bar, after the Obys DES project index. Pure CSS and a Server Component; works with or without Tailwind, and is keyboard and touch safe.

## With Claude Code

```
/animations:list-hover-sliding-fill the project index on the home page
```

The skill is [`skills/list-hover-sliding-fill.md`](../../skills/list-hover-sliding-fill.md). It checks your project first, writes these files where your project keeps components, uses the component where you ask, and runs its own checks.

## Without it

| File | Where it goes |
|---|---|
| `SlidingFillList.tsx` | `components/ui/` (or `src/components/ui/`) |
| `SlidingFillList.css` | `components/ui/` (or `src/components/ui/`); in the Pages Router, import it in `pages/_app.tsx` |

Needs: Nothing.

The skill file explains the rest: the props, the values and why they were chosen, and the ways it breaks.

## Tested

`harness.py list tuned`, `list_extra.py` in [`tests/`](../../tests/), on three fresh projects (App Router with Tailwind v4 and v3, Pages Router without Tailwind), in dev and production, in Chromium, Firefox and WebKit.
