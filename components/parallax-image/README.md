# Parallax image

<img src="../../media/parallax-image.gif" alt="Parallax image: Drift, zoom and settle on one page." width="100%">

A photograph moves inside a still frame as the frame crosses the screen, in one of three variants: drift; zoom (1.45 to 1, measured on Telha Clarke); settle (1.12 to 1 over 1.8 s, measured on OH Architecture). Wraps any `img`, `next/image` or `video`, and the picture always covers its frame.

## With Claude Code

```
/animations:parallax-image the project hero images, drift
```

The skill is [`skills/parallax-image.md`](../../skills/parallax-image.md). It checks your project first, writes these files where your project keeps components, uses the component where you ask, and runs its own checks.

## Without it

| File | Where it goes |
|---|---|
| `ParallaxImage.tsx` | `components/ui/` (or `src/components/ui/`) |

Needs: `gsap` and `@gsap/react`.

The skill file explains the rest: the props, the values and why they were chosen, and the ways it breaks.

## Tested

`parallax_extra.py` in [`tests/`](../../tests/), on three fresh projects (App Router with Tailwind v4 and v3, Pages Router without Tailwind), in dev and production, in Chromium, Firefox and WebKit.
