---
description: Wipe button (DES). A button whose fill only ever travels one way. On hover the fill leaves through the top; on leave it comes back in from the bottom; the label crossfades in step. Timing measured from des.obys.agency. Link or button, any size, keyboard and touch safe; for Next.js (App or Pages Router) + GSAP.
argument-hint: "[optional: where to use it, e.g. 'the Log In and Book a call buttons in components/Header.tsx']"
model: claude-opus-5-5
effort: max
---

# Wipe button (DES)

Build the wipe button in the current project and use it where `$ARGUMENTS` says. If `$ARGUMENTS` is empty, create the component and show it as a "Log In" button in a header and a larger call to action.

## What it looks like
At rest it's a solid ink button with white text, a 1.5px border and a small radius. Point at it and the fill slides up and out through the top edge in 221ms, uncovering an outline button with ink text; the text crossfades from white to ink as the fill passes. Move off and the fill comes back in from the bottom edge in 207ms, rising until it covers the button again. The fill never reverses: it always travels up, so in and out read as one continuous stream. Move in and out quickly and it still never runs backwards; a second fill panel takes over behind the first. This is the "Log In" button on des.obys.agency, measured frame by frame at 60fps.

Options: `rest="outline"` starts clear and fills on hover (the DES call-to-action, with `preset="cta"`: 500ms in, 400ms out on expo.out). `direction="down"` sends the fill top to bottom instead.

## Before you write code
1. **GSAP.** Check `package.json` for `gsap` (3.12 or later). If it's missing, run `npm install gsap`. No other package is needed, and no GSAP plugin.
2. **The components folder.** Read `tsconfig.json` (or `jsconfig.json`) `compilerOptions.paths` and put the file wherever `@/components/...` resolves: `components/ui/` at the root, or `src/components/ui/`. In a JavaScript project, save it as `WipeButton.jsx` and drop the types.
3. **Colours.** Find the page's ink and background colours (global CSS or the Tailwind theme) and pass them as `ink` and `paper`. The defaults are `#17191a` and `#ffffff`. They're plain colour props on purpose: GSAP tweens the label between them, and a Tailwind class can't be tweened.
4. **Links or buttons.** With `href` it renders a Next.js `Link`; without, a `<button>` (use `type="submit"` in a form). The label must be a string.

## Build

### 1. The component: `components/ui/WipeButton.tsx`
It's a Client Component (`"use client"`); you can render it from Server Components. All of its styling is inline, so it needs no CSS file in either router and doesn't depend on Tailwind.
```tsx
"use client";

import Link from "next/link";
import { useEffect, useRef, type CSSProperties, type MouseEventHandler, type Ref } from "react";
import gsap from "gsap";

type Timing = { duration: number; ease: string };

// Measured frame by frame from des.obys.agency at 60 fps.
const PRESETS = {
  // the "Log In" button: the fill leaves in 221 ms (sine.in) and comes back in 207 ms (sine.out)
  login: { clear: { duration: 0.22, ease: "sine.in" }, cover: { duration: 0.21, ease: "sine.out" } },
  // the larger call-to-action: 500 ms in, 400 ms out, on expo.out (cubic-bezier(0.16, 1, 0.3, 1))
  cta: { clear: { duration: 0.4, ease: "expo.out" }, cover: { duration: 0.5, ease: "expo.out" } },
} satisfies Record<string, { clear: Timing; cover: Timing }>;

type WipeButtonProps = {
  children: string;
  /** with href it renders a Next.js Link; without, a <button> */
  href?: string;
  onClick?: MouseEventHandler<HTMLElement>;
  type?: "button" | "submit";
  target?: string;
  rel?: string;
  id?: string;
  className?: string;
  style?: CSSProperties;
  preset?: keyof typeof PRESETS;
  /** filled: solid at rest, hover clears it. outline: clear at rest, hover fills it. */
  rest?: "filled" | "outline";
  /** the one direction the fill ever travels */
  direction?: "up" | "down";
  ink?: string;
  paper?: string;
  radius?: string;
};

export default function WipeButton({
  children,
  href,
  onClick,
  type = "button",
  target,
  rel,
  id,
  className,
  style,
  preset = "login",
  rest = "filled",
  direction = "up",
  ink = "#17191a",
  paper = "#ffffff",
  radius = "0.45em",
}: WipeButtonProps) {
  const root = useRef<HTMLElement>(null);
  const panelA = useRef<HTMLSpanElement>(null);
  const panelB = useRef<HTMLSpanElement>(null);
  const label = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const el = root.current!;
    const panels = [panelA.current!, panelB.current!];
    const text = label.current!;
    const s = direction === "down" ? 1 : -1; // the sign of "forward" in yPercent
    const timing = PRESETS[preset];
    const still = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let active = 0;

    // A panel's forward progress: -101 waiting at the entry edge, 0 covering, 101 gone out the exit edge.
    const progress = (i: number) => (gsap.getProperty(panels[i], "yPercent") as number) * s;
    const place = (i: number, p: number) => gsap.set(panels[i], { yPercent: p * s });
    const move = (i: number, p: number, t: Timing) =>
      still() ? place(i, p) : gsap.to(panels[i], { yPercent: p * s, duration: t.duration, ease: t.ease, overwrite: true });
    const tint = (covered: boolean, t: Timing) =>
      gsap.to(text, { color: covered ? paper : ink, duration: still() ? 0 : t.duration, ease: t.ease, overwrite: true });

    // The server already parked the panels with a CSS transform. Hand that over to GSAP as yPercent and zero
    // the px offset GSAP parsed from it, or the two would add up.
    gsap.set(panels, { y: 0 });
    place(0, rest === "filled" ? 0 : -101);
    place(1, -101);

    const cover = () => {
      if (progress(active) <= 0) {
        move(active, 0, timing.cover); // still arriving, or waiting: keep coming forward
      } else {
        // the active panel is on its way out: let it go, and bring the other one in behind it
        active = 1 - active;
        place(active, -101);
        move(active, 0, timing.cover);
      }
      tint(true, timing.cover);
    };
    const clear = () => {
      move(active, 101, timing.clear); // always forward, out through the exit edge
      tint(false, timing.clear);
    };

    let hovered = false;
    let focused = false;
    let covered = rest === "filled";
    const sync = () => {
      const want = rest === "filled" ? !(hovered || focused) : hovered || focused;
      if (want === covered) return;
      covered = want;
      if (want) cover();
      else clear();
    };
    // Touch is ignored on purpose: a tap should just follow the link, not leave a half-wiped button behind.
    const enter = (e: PointerEvent) => {
      if (e.pointerType === "touch") return;
      hovered = true;
      sync();
    };
    const leave = (e: PointerEvent) => {
      if (e.pointerType === "touch") return;
      hovered = false;
      sync();
    };
    const focus = () => {
      focused = el.matches(":focus-visible"); // the keyboard, not the focus a mouse click leaves behind
      sync();
    };
    const blur = () => {
      focused = false;
      sync();
    };

    el.addEventListener("pointerenter", enter);
    el.addEventListener("pointerleave", leave);
    el.addEventListener("focus", focus);
    el.addEventListener("blur", blur);
    return () => {
      el.removeEventListener("pointerenter", enter);
      el.removeEventListener("pointerleave", leave);
      el.removeEventListener("focus", focus);
      el.removeEventListener("blur", blur);
      gsap.killTweensOf([...panels, text]);
    };
  }, [preset, rest, direction, ink, paper]);

  // Where each panel sits before JavaScript runs: so the first paint is already right.
  const waiting = `translateY(${direction === "down" ? "-101%" : "101%"})`;
  const panel: CSSProperties = { position: "absolute", inset: 0, background: ink, pointerEvents: "none" };
  const box: CSSProperties = {
    position: "relative",
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "0.75em 1.2em",
    border: `1.5px solid ${ink}`,
    borderRadius: radius,
    overflow: "hidden",
    isolation: "isolate",
    background: paper,
    color: ink,
    font: "inherit",
    lineHeight: 1,
    textDecoration: "none",
    cursor: "pointer",
    ...style,
  };
  const inner = (
    <>
      <span ref={panelA} aria-hidden="true" style={{ ...panel, transform: rest === "filled" ? undefined : waiting }} />
      <span ref={panelB} aria-hidden="true" style={{ ...panel, transform: waiting }} />
      <span ref={label} style={{ position: "relative", color: rest === "filled" ? paper : ink }}>
        {children}
      </span>
    </>
  );

  return href ? (
    <Link ref={root as Ref<HTMLAnchorElement>} href={href} id={id} className={className} style={box} target={target} rel={rel} onClick={onClick}>
      {inner}
    </Link>
  ) : (
    <button ref={root as Ref<HTMLButtonElement>} type={type} id={id} className={className} style={box} onClick={onClick}>
      {inner}
    </button>
  );
}
```

### 2. Use it
```tsx
import WipeButton from "@/components/ui/WipeButton";

<WipeButton href="/login">Log In</WipeButton>

<WipeButton href="/contact" preset="cta" rest="outline">Begin a project</WipeButton>

<WipeButton type="submit" direction="down" radius="0">Send</WipeButton>
```
It takes its size from its parent's `font-size` (padding and radius are in `em`), so wrap it or pass `style={{ fontSize: 22 }}` to scale it. Use `style` for spacing or a fixed width; don't override `position`, `overflow` or `background`, which the wipe relies on.

## Why these values
- **221ms out on `sine.in`, 207ms back on `sine.out`:** fitted to the DES capture (about 1% error over the travel). The fill accelerates as it leaves and decelerates as it lands, so leaving reads as a release and returning reads as settling. Both are short: this is a control, not a reveal.
- **One direction only.** A fill that runs back the way it came reads as a cancelled action. Travelling on through reads as one stream, and that's the whole character of the DES button.
- **Two panels.** If the pointer comes back while the fill is still leaving, the leaving panel keeps going and the second one arrives behind it from the entry edge. Nothing reverses and nothing teleports while it's visible.
- **The panels are parked by CSS on the server render.** The first paint is already correct. A button that is clear at rest never flashes filled before JavaScript loads.
- **`:focus-visible` for the keyboard.** Tabbing to it plays the wipe. The focus a mouse click leaves behind doesn't, or the button would stay clear after the pointer left.
- **Touch is ignored.** A tap fires pointer events in and out within a few milliseconds. A wipe there would flicker, so a tap just follows the link.

## Failure patterns to avoid
Measured on Next.js 16.3.8 with GSAP 3.15, in Chromium, Firefox and WebKit, 2026-10-05:
- **One panel that tweens back and forth (or a CSS transition on the fill).** In the release suite, leaving mid-wipe made the fill crawl back down (for example from −14.2px to −12.3px) in all three engines, and the "comes back from below" check failed in all three. Keep the two-panel logic as written.
- **Parking the panels only in JavaScript.** Before hydration, both panels cover the button, so a `rest="outline"` button paints filled first. Park them with the inline `transform` the component sets.
- **Letting GSAP read that inline `translateY(…%)`.** GSAP parses it into a pixel `y` and then adds `yPercent` on top, so the panel lands twice as far away. The component zeroes `y` before it takes over.
- **Plain `focus`/`blur` in place of `:focus-visible`.** After a mouse click the link keeps focus, so the button stays clear when the pointer leaves.
- **Hover handlers that also fire on touch.** A tap leaves a half-wiped button or a flicker. Touch pointers are skipped.

## Verify before you finish
Run each check, fix anything that fails, and say which ones you ran:
1. `npx tsc --noEmit` and `npm run build` both succeed.
2. View the page source (or `curl` the page): the button's label is in the HTML, and its panels carry `translateY(101%)` (or `-101%` with `direction="down"`).
3. Hover: the fill leaves through the top edge (or the bottom with `direction="down"`), the text turns ink, and moving off brings the fill back from the other edge.
4. Move in and out as fast as you can, several times: the fill never runs backwards and never jumps while visible. It ends filled once the pointer is away.
5. Tab to it: it wipes. Tab away: it refills. Click it, then move the mouse away: it refills.
6. In device emulation (touch), tap it: nothing stays half-wiped.
7. With `prefers-reduced-motion: reduce` emulated, hover swaps the state at once with no in-between frames.
