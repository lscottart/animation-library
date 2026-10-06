# Number roll

<img src="../../media/number-roll.gif" alt="Number roll: Last light at each house." width="100%">

Digits roll to a new value like a counter, right-most first, while colons, commas and letters stay put. The value is real text in the page once; the rolling strips are generated content. CSS transitions, no library.

## With Claude Code

```
/animations:number-roll the local time in the footer
```

The skill is [`skills/number-roll.md`](../../skills/number-roll.md). It checks your project first, writes these files where your project keeps components, uses the component where you ask, and runs its own checks.

## Without it

| File | Where it goes |
|---|---|
| `NumberRoll.tsx` | `components/ui/` (or `src/components/ui/`) |
| `NumberRoll.css` | `components/ui/` (or `src/components/ui/`); in the Pages Router, import it in `pages/_app.tsx` |

Needs: Nothing.

The skill file explains the rest: the props, the values and why they were chosen, and the ways it breaks.

## Tested

`numroll_extra.py` in [`tests/`](../../tests/), on three fresh projects (App Router with Tailwind v4 and v3, Pages Router without Tailwind), in dev and production, in Chromium, Firefox and WebKit.
