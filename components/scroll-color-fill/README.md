# Scroll color fill

<img src="../../media/scroll-color-fill.gif" alt="Scroll color fill: The studio statement." width="100%">

A statement fills from grey to ink, character by character, at the reader's own scroll pace. The characters are split in React on the server, so the sentence is in the HTML, nothing rewrites the DOM, and accents, emoji and flags fill as one piece.

## With Claude Code

```
/animations:scroll-color-fill the studio statement on the about page
```

The skill is [`skills/scroll-color-fill.md`](../../skills/scroll-color-fill.md). It checks your project first, writes these files where your project keeps components, uses the component where you ask, and runs its own checks.

## Without it

| File | Where it goes |
|---|---|
| `ScrollColorFill.tsx` | `components/ui/` (or `src/components/ui/`) |
| `ScrollColorFill.css` | `components/ui/` (or `src/components/ui/`); in the Pages Router, import it in `pages/_app.tsx` |

Needs: `gsap` and `@gsap/react`.

The skill file explains the rest: the props, the values and why they were chosen, and the ways it breaks.

## Tested

`colorfill_extra.py` in [`tests/`](../../tests/), on three fresh projects (App Router with Tailwind v4 and v3, Pages Router without Tailwind), in dev and production, in Chromium, Firefox and WebKit.
