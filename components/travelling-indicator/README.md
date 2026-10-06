# Travelling indicator

<img src="../../media/travelling-indicator.gif" alt="Travelling indicator: The menu block and the image tools." width="100%">

One highlight travels between a nav's items, a set of filters or a toolbar's buttons and resizes to each, instead of every item owning its own hover. An ink block with the text inverting inside it, a hairline underline, or one tooltip that slides between buttons. Right on first paint, keyboard aware.

## With Claude Code

```
/animations:travelling-indicator the header nav, block
```

The skill is [`skills/travelling-indicator.md`](../../skills/travelling-indicator.md). It checks your project first, writes these files where your project keeps components, uses the component where you ask, and runs its own checks.

## Without it

| File | Where it goes |
|---|---|
| `TravellingIndicator.tsx` | `components/ui/` (or `src/components/ui/`) |
| `TravellingIndicator.css` | `components/ui/` (or `src/components/ui/`); in the Pages Router, import it in `pages/_app.tsx` |

Needs: `gsap`.

The skill file explains the rest: the props, the values and why they were chosen, and the ways it breaks.

## Tested

`travel_extra.py` in [`tests/`](../../tests/), on three fresh projects (App Router with Tailwind v4 and v3, Pages Router without Tailwind), in dev and production, in Chromium, Firefox and WebKit.
