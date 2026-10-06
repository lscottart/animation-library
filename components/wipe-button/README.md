# Wipe button

<img src="../../media/wipe-button.gif" alt="Wipe button: In, out, and straight back in." width="100%">

The des.obys.agency "Log In" button: hover sends the fill out the top, leaving brings it back in from the bottom, and the label crossfades in step. Timing measured frame by frame from a capture (out 221 ms, back 207 ms). Two panels, so it never reverses, however fast you come and go.

## With Claude Code

```
/animations:wipe-button the Book a call button in the footer
```

The skill is [`skills/wipe-button.md`](../../skills/wipe-button.md). It checks your project first, writes these files where your project keeps components, uses the component where you ask, and runs its own checks.

## Without it

| File | Where it goes |
|---|---|
| `WipeButton.tsx` | `components/ui/` (or `src/components/ui/`) |

Needs: `gsap`.

The skill file explains the rest: the props, the values and why they were chosen, and the ways it breaks.

## Tested

`wipe_extra.py` in [`tests/`](../../tests/), on three fresh projects (App Router with Tailwind v4 and v3, Pages Router without Tailwind), in dev and production, in Chromium, Firefox and WebKit.
