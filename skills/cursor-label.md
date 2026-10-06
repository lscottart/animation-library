---
description: Cursor label. A word like "(View)" rolls into a one-line window at the cursor whenever it's over an element marked data-cursor-label, trails the pointer with a soft lag, and rolls out when it leaves. One global component, any number of targets, legible on photos and paper. For Next.js (App or Pages Router) + GSAP.
argument-hint: "[optional: where to use it and the labels, e.g. 'the project grid on app/work/page.tsx: (View project)']"
model: claude-opus-5-5
effort: max
---

# Cursor label

Build the cursor label in the current project and use it where `$ARGUMENTS` says. If `$ARGUMENTS` is empty, create the component, mount it once, and label a grid of three project images "(View project)".

## What it looks like
Move the pointer onto a labelled element (a project image, a video, a card) and a short label appears just to the right of the cursor. It doesn't fade: it rolls up into a one-line window in 0.4s on expo.out. It then trails the pointer on a soft lag; the vertical lag is a little slower than the horizontal, so it floats rather than sticks. Move straight onto another labelled element and the first label rolls up and out before the next one rolls in from below. Two labels never overlap and a label never replays. Come back to the same element while its label is leaving and the roll catches and settles back, instead of starting over. Move off, or scroll the element out from under a still pointer, and it rolls out. The label is white with a `difference` blend, so it inverts against whatever is under it: dark on a light page, light on a dark photograph. It never blocks a click. It only runs for a mouse or trackpad: there's no label on touch screens or under reduced motion. The mechanic is the "(View)" label on des.obys.agency, rebuilt from how it behaves, not from its code.

## Before you write code
1. **GSAP.** Check `package.json` for `gsap` (3.12 or later). If it's missing, run `npm install gsap`. No plugins are needed.
2. **The components folder.** Read `tsconfig.json` (or `jsconfig.json`) `compilerOptions.paths` and put the file wherever `@/components/...` resolves: `components/ui/` at the root, or `src/components/ui/`. In a JavaScript project, save it as `CursorLabel.jsx` and drop the types.
3. **Mount it once.** One `<CursorLabel />` serves every labelled element on the page. Put it in the layout (`app/layout.tsx`, or `pages/_app.tsx` in the Pages Router), or on the one page that uses it. Two instances would draw two labels.
4. **The targets.** Add `data-cursor-label="(View project)"` to each element that should show a label. The attribute's text is the label, so different targets can say different things. The label sits at the cursor, offset 18px right and 10px up. Pass `offsetX` and `offsetY` to change that.
5. **The type.** The label inherits the page's font. To size or style it, pass a `className` (or set `[data-cursor-label-root] { … }` in CSS); keep it small, 14 to 16px.

## Build

### 1. The component: `components/ui/CursorLabel.tsx`
It's a Client Component; it renders nothing visible until a labelled element is under the cursor.
```tsx
"use client";

import { useEffect, useRef } from "react";
import gsap from "gsap";

// The trail: x catches up a little faster than y, so the label floats as it follows (Obys DES).
const X_LERP = 0.11;
const Y_LERP = 0.085;

type Props = {
  /** where the label sits relative to the pointer, in px */
  offsetX?: number;
  offsetY?: number;
  /** white with a difference blend inverts against whatever is under it, so it reads on photos and on paper */
  blend?: boolean;
  className?: string;
};

export default function CursorLabel({ offsetX = 18, offsetY = -10, blend = true, className }: Props) {
  const rootRef = useRef<HTMLDivElement>(null);
  const textRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    // Mouse and trackpad only. On touch there's no hover to label, and under reduced motion it stays off.
    const fine = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
    const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!fine || still) return;
    const root = rootRef.current!;
    const text = textRef.current!;
    const setX = gsap.quickSetter(root, "x", "px");
    const setY = gsap.quickSetter(root, "y", "px");
    const pos = { x: -200, y: -200 };
    const target = { x: -200, y: -200 };
    const pointer = { x: -1, y: -1 };
    gsap.set(text, { yPercent: 110 }); // the label waits below its window
    gsap.set(root, { x: pos.x, y: pos.y, visibility: "visible" });

    // The exit always finishes before the next entry (a direct jump between two labelled items queues the
    // second), and coming back to the same item mid-exit catches the roll instead of replaying it.
    let state: "hidden" | "shown" | "exiting" = "hidden";
    let shownFor: Element | null = null;
    let pending: Element | null = null;

    const enter = (item: Element) => {
      state = "shown";
      shownFor = item;
      pending = null;
      text.textContent = item.getAttribute("data-cursor-label") || "(View)";
      // appear where the pointer is, then roll in: no fly-in from the last spot
      pos.x = target.x;
      pos.y = target.y;
      setX(pos.x);
      setY(pos.y);
      gsap.killTweensOf(text);
      gsap.fromTo(text, { yPercent: 110 }, { yPercent: 0, duration: 0.4, ease: "expo.out" });
    };
    const exit = () => {
      state = "exiting";
      gsap.killTweensOf(text);
      gsap.to(text, {
        yPercent: -110,
        duration: 0.3,
        ease: "expo.out",
        onComplete: () => {
          state = "hidden";
          shownFor = null;
          if (pending) {
            const next = pending;
            pending = null;
            enter(next);
          }
        },
      });
    };
    const evaluate = (el: Element | null) => {
      const item = el ? el.closest("[data-cursor-label]") : null;
      if (state === "shown") {
        if (item === shownFor) return;
        if (item) pending = item;
        exit();
      } else if (state === "exiting") {
        if (item === shownFor) {
          state = "shown";
          pending = null;
          gsap.killTweensOf(text);
          gsap.to(text, { yPercent: 0, duration: 0.25, ease: "expo.out" });
        } else {
          pending = item; // the next item waits; null cancels the queue
        }
      } else if (item) {
        enter(item);
      }
    };

    const onMove = (e: PointerEvent) => {
      if (e.pointerType === "touch") return;
      pointer.x = e.clientX;
      pointer.y = e.clientY;
      target.x = e.clientX + offsetX;
      target.y = e.clientY + offsetY;
      evaluate(e.target as Element);
    };
    // Scrolling moves the page under a still pointer (smooth-scroll libraries send no pointer events), so check
    // again what's beneath it.
    const onScroll = () => {
      if (pointer.x >= 0) evaluate(document.elementFromPoint(pointer.x, pointer.y));
    };
    const onLeaveWindow = () => evaluate(null);
    const tick = () => {
      pos.x += (target.x - pos.x) * X_LERP;
      pos.y += (target.y - pos.y) * Y_LERP;
      setX(pos.x);
      setY(pos.y);
    };

    document.addEventListener("pointermove", onMove, { passive: true });
    window.addEventListener("scroll", onScroll, { passive: true });
    document.documentElement.addEventListener("mouseleave", onLeaveWindow);
    gsap.ticker.add(tick);
    return () => {
      document.removeEventListener("pointermove", onMove);
      window.removeEventListener("scroll", onScroll);
      document.documentElement.removeEventListener("mouseleave", onLeaveWindow);
      gsap.ticker.remove(tick);
      gsap.killTweensOf(text);
    };
  }, [offsetX, offsetY]);

  return (
    <div
      ref={rootRef}
      data-cursor-label-root=""
      aria-hidden="true"
      className={className}
      style={{
        position: "fixed",
        left: 0,
        top: 0,
        zIndex: 100,
        pointerEvents: "none",
        visibility: "hidden",
        whiteSpace: "nowrap",
        color: blend ? "#fff" : undefined,
        mixBlendMode: blend ? "difference" : undefined,
      }}
    >
      {/* the one-line window the label rolls through */}
      <span style={{ display: "block", overflow: "hidden", lineHeight: 1.3 }}>
        <span ref={textRef} style={{ display: "block" }}>
          (View)
        </span>
      </span>
    </div>
  );
}
```

### 2. Use it
```tsx
// app/layout.tsx (or one page)
import CursorLabel from "@/components/ui/CursorLabel";

<body>
  {children}
  <CursorLabel />
</body>

// anywhere
<a href="/work/harlan" data-cursor-label="(View project)">
  <img src="/work/harlan.jpg" alt="Harlan House" />
</a>
<div data-cursor-label="(Play)">…</div>
```
Use `blend={false}` and a `className` with your own colour if the difference blend clashes with a coloured background.

## Why these values
- **Rolling, not fading:** the label enters through a one-line window, like a type slug, which is the DES detail. A fade-in reads as a tooltip.
- **0.4s in, 0.3s out, expo.out:** fast to arrive, quick to clear, with no slow tail that would leave a ghost behind a fast-moving pointer.
- **Lerp 0.11 horizontally and 0.085 vertically:** the label follows a step behind and floats. Equal values stick it to the cursor; much lower drags it.
- **The exit always finishes before the next label enters:** two labels never fight in the window. Re-entering the same item catches the roll, so it can never play twice for one item.
- **Checking again on scroll:** smooth-scroll libraries move the page without pointer events. Without the check, the label would keep saying "(View)" over empty space.
- **White with a `difference` blend:** a single label that reads on paper and on photographs. Dark ink alone vanishes on a twilight photograph.

## Failure patterns to avoid
Measured on Next.js 16.3.8 with GSAP 3.15, in Chromium, Firefox and WebKit, 2026-10-05:
- **Entering the next label immediately on a direct jump.** With the queue removed, moving between two labelled items that touch (no gap to cross) swapped the label in place. The old one vanished mid-window and the new one rose over it. Coming back to an item mid-exit replayed the roll from below (it reached 0.8 to 0.95 of its height). Both checks failed in Chromium, Firefox and WebKit. A grid with gaps hides this bug, because crossing the gap runs the normal exit first. Keep the queue.
- **Dark text without the blend.** The label disappears over dark photographs. (A guard, not measured.)
- **Finding the label by its inline style in tests or CSS.** React's server markup writes `position:fixed` with no space, and the browser rewrites it once GSAP touches the element. Use the `data-cursor-label-root` hook.
- **Listening only to `pointermove`.** With a still pointer, scrolling (especially with a smooth-scroll library) moves the page without a pointer event, so the label would hang over nothing. The scroll check covers it, and the suite confirms the label retires when its item scrolls away. Not measured with the check removed.

## Verify before you finish
Run each check, fix anything that fails, and say which ones you ran:
1. `npx tsc --noEmit` and `npm run build` both succeed.
2. Move onto a labelled element: the label rolls in beside the cursor, shows that element's text, and trails the pointer a step behind.
3. Move straight to a second labelled element: the first label leaves, then the second rolls in. They never overlap.
4. Move off and come straight back: the label settles back without replaying.
5. Rest the pointer on an element and scroll it away: the label rolls out.
6. Click through the label: the element under it receives the click.
7. Over a dark image and over the light page, the label is readable.
8. In device emulation (touch), and with `prefers-reduced-motion: reduce` emulated, no label appears.
