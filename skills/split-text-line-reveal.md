---
description: Split text line reveal. Each line of a heading or paragraph rises out of its own mask, staggered (GSAP SplitText). For Next.js (App or Pages Router) + GSAP 3.13+. Safe in Server Components, starts from the very bottom of its rise even on a busy page, and hands the text back to React when it lands, so links and updates inside keep working.
argument-hint: "[optional: where to use it, e.g. 'the h1 and intro paragraph on app/page.tsx']"
model: claude-opus-5-5
effort: max
---

# Split text line reveal

Build the split text line reveal in the current project, then use it where `$ARGUMENTS` says. If `$ARGUMENTS` is empty, create the component and show it working on one heading and one paragraph.

## What it looks like
Each line of a text block starts below its own invisible mask and rises into place. The motion is fast at first and settles slowly (`power4.out`, 1 s per line), and the lines start 0.1 s apart, so the block reads top to bottom. The text is never visible before its reveal, and the first moving frame is the very start of the rise, even while the page is still busy loading. Once every line has landed, the element is plain text again, in the DOM nodes React rendered: it reflows on resize like any paragraph, screen readers read it normally, links inside route client-side, and keyboard focus stays where it was. Text below the fold waits until it scrolls into view, 90% down the viewport.

## Before you write code
Read these first, because they decide where the files go and whether anything needs installing:
1. **`package.json`.** You need `gsap` 3.13 or later and `@gsap/react`. SplitText, its `mask` option and `autoSplit` ship inside `gsap` from 3.13 and are free. If either is missing or older, run `npm install gsap@latest @gsap/react`. Don't install `split-type` or any other splitter.
2. **The components folder.** Read `tsconfig.json` (or `jsconfig.json`) `compilerOptions.paths`. Put the component wherever `@/components/...` resolves: `components/ui/` at the root, or `src/components/ui/` in a `src/` project. In a JavaScript project, save it as `SplitReveal.jsx` and drop the type annotations.
3. **The router.** `app/` means the App Router, which these instructions assume. In the Pages Router, put the CSS in the global stylesheet imported by `pages/_app.tsx`, and put the `<noscript>` line in `pages/_document.tsx`.
4. **Existing reveal code.** If the project already has a split or reveal component, replace its uses with this one rather than running two systems.

## Build

### 1. The component: `components/ui/SplitReveal.tsx`
```tsx
"use client";

import { useRef, type ComponentPropsWithoutRef, type ElementType } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { SplitText } from "gsap/SplitText";
import { useGSAP } from "@gsap/react";

gsap.registerPlugin(useGSAP, ScrollTrigger, SplitText);

// SplitText's revert() rebuilds the element from an HTML string, which swaps out the DOM nodes React rendered.
// React keeps editing the old ones, so links stop routing client-side, onClick stops firing, and the next change
// to the text crashes. This records React's nodes and returns a function that puts them back.
function keepReactNodes(root: Element) {
  const children = new Map<Element, ChildNode[]>();
  const texts = new Map<Text, string>();
  const record = (parent: Element) => {
    children.set(parent, Array.from(parent.childNodes));
    parent.childNodes.forEach((node) => {
      if (node.nodeType === Node.TEXT_NODE) texts.set(node as Text, (node as Text).data);
      else if (node.nodeType === Node.ELEMENT_NODE) record(node as Element);
    });
  };
  record(root);
  return () => {
    children.forEach((nodes, parent) => parent.replaceChildren(...nodes));
    texts.forEach((data, node) => (node.data = data)); // SplitText edits text nodes as it splits them
  };
}

// Moving the nodes drops keyboard focus, so put it back. A link that wraps was split into SplitText's copies
// (one per line) and React's original (the last line), so focus on a copy goes to the original.
function refocus(root: Element, focused: HTMLElement | null) {
  if (!focused || document.activeElement === focused) return;
  const target = root.contains(focused)
    ? focused
    : Array.from(root.querySelectorAll<HTMLElement>(focused.tagName)).find((n) =>
        n.cloneNode().isEqualNode(focused.cloneNode()),
      );
  target?.focus({ preventScroll: true });
}

type SplitRevealProps<T extends ElementType> = {
  /** The element to render: "h1", "p", "h2"… (default "p") */
  as?: T;
  /** "scroll": reveal when the element reaches `start`. "load": reveal as soon as it's ready. */
  trigger?: "scroll" | "load";
  delay?: number;
  duration?: number;
  stagger?: number;
  ease?: string;
  /** ScrollTrigger start, "element-edge viewport-edge" */
  start?: string;
} & Omit<ComponentPropsWithoutRef<T>, "as">;

export default function SplitReveal<T extends ElementType = "p">({
  as,
  trigger = "scroll",
  delay = 0,
  duration = 1,
  stagger = 0.1,
  ease = "power4.out",
  start = "top 90%",
  children,
  ...rest
}: SplitRevealProps<T>) {
  const Tag: ElementType = as ?? "p";
  const ref = useRef<HTMLElement>(null);

  useGSAP(
    (_context, contextSafe) => {
      const el = ref.current;
      if (!el) return;
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        gsap.set(el, { visibility: "visible" });
        return;
      }
      let live = true;
      let stop: (() => void) | undefined;
      // Created after an await, so it must run through contextSafe: that records the split, its tween and its
      // ScrollTrigger in this component's context, and unmounting reverts all three.
      const reveal = contextSafe!(() => {
        if (!live) return;
        let started = trigger === "scroll"; // a scroll reveal is started by its ScrollTrigger
        let tween: gsap.core.Tween | undefined;
        SplitText.create(el, {
          type: "lines",
          mask: "lines",
          linesClass: "split-line",
          autoSplit: true, // re-splits if the width changes or a font arrives before the reveal
          // aria "auto" labels the element and hides the lines, which would also hide any link inside it
          aria: el.querySelector("a, button, input, select, textarea, [tabindex]") ? "none" : "auto",
          onRevert: keepReactNodes(el), // after every revert, autoSplit's re-splits included
          onSplit(self) {
            // Each mask clips 0.3em beyond its line box (a clip-path, which changes no layout), so tight leading
            // never cuts descenders or accents, and each line starts that much further down, so nothing peeks out.
            const room = 0.3 * parseFloat(getComputedStyle(el).fontSize);
            (self.masks as HTMLElement[]).forEach((mask) => {
              mask.style.overflow = "visible";
              mask.style.clipPath = `inset(-${room}px -1em -${room}px -1em)`;
            });
            tween = gsap.from(self.lines, {
              y: (_i: number, line: HTMLElement) => line.offsetHeight + 2 * room,
              duration,
              stagger,
              ease,
              delay,
              paused: !started,
              scrollTrigger: trigger === "scroll" ? { trigger: el, start, once: true } : undefined,
              onComplete: () => {
                const focused = el.contains(document.activeElement) ? (document.activeElement as HTMLElement) : null;
                self.revert(); // plain text again: reflows on resize, reads normally
                refocus(el, focused);
              },
            });
            gsap.set(el, { visibility: "visible" }); // the CSS hid it until the lines were below their masks
            return tween; // returned so autoSplit can re-split and carry the progress over
          },
        });
        if (!started) {
          // GSAP times a new tween from the last frame it rendered, so main-thread work since then (hydration, a
          // WebGL scene starting up) would cut off the start of the motion. Start it on the second frame instead: the
          // first still has to lay out and paint the split lines (many lines, fallback fonts), which can take longer
          // than a frame, and that time would count as motion too.
          let ticks = 0;
          const go = () => {
            if (++ticks < 2) return;
            gsap.ticker.remove(go);
            started = true;
            if (live) tween?.play();
          };
          gsap.ticker.add(go);
          stop = () => gsap.ticker.remove(go);
        }
      });
      document.fonts.ready.then(reveal); // split with the final font's line breaks
      return () => {
        live = false;
        stop?.();
      };
    },
    { scope: ref, dependencies: [trigger, delay, duration, stagger, ease, start] },
  );

  return (
    <Tag ref={ref} data-split-reveal="" {...rest}>
      {children}
    </Tag>
  );
}
```

### 2. The CSS, in the global stylesheet (`app/globals.css`)
```css
/* SplitReveal: hidden until split, so the unsplit text never flashes */
[data-split-reveal] {
  visibility: hidden;
}
```

### 3. The no-JavaScript fallback, in the root layout's `<head>` (`app/layout.tsx`)
```tsx
<noscript>
  <style>{`[data-split-reveal]{visibility:visible!important}`}</style>
</noscript>
```
If the layout has no `<head>` element, add one inside `<html>`, before `<body>`.

### 4. Use it
The component renders its own element, so put the text inside it. It works in Server Components. Pass `id`, `className`, `style` or any other attribute straight through:
```tsx
import SplitReveal from "@/components/ui/SplitReveal";

<SplitReveal as="h1" trigger="load" delay={0.2} className="hero-title">
  Glyphs hang, typography lands.
</SplitReveal>

<SplitReveal>
  Body copy reveals line by line when it scrolls into view, links and <em>emphasis</em> included.
</SplitReveal>
```
Wrap the text, not a component tree. Inline elements inside (links, `em`, `strong`, `br`) are fine. Block elements (`div`, `p`) inside one `SplitReveal` aren't: give each block its own.

The text should stay the same while it's split, which for text below the fold is from page load until its reveal ends. If it can change in that time (state, a language switch), give `SplitReveal` a `key` that changes with it, so React replaces the element instead of editing split DOM: `<SplitReveal key={locale}>…</SplitReveal>`.

## Why these values
- **`power4.out`, 1 s:** in GSAP's naming `powerN` has exponent N+1, so this is the quint ease-out, `1 − (1 − t)⁵`. The line covers two thirds of its travel in the first fifth of a second, then settles, so it lands with weight. `power2` reads soft, and a linear ease reads mechanical. For long body copy, `duration={0.75}` keeps paragraphs from dragging.
- **0.1 s stagger:** the eye follows one line to the next without waiting. Below 0.05 s the lines move as a block; above 0.15 s the reveal drags.
- **The masks clip 0.3em beyond each line, with a `clip-path`:** tight display leading (`line-height` 1 or lower) puts descenders and accents outside the line box, and a plain `overflow: clip` mask cuts them off at the end of the reveal. A `clip-path` with negative insets gives them room without touching layout. Padding with a negative margin also gives room, but adjacent negative margins collapse, so every line drifts lower.
- **Each line starts `line height + 0.6em` down:** that clears the extended clip, so not a sliver shows before the reveal at any font size or leading. The extra distance passes in the first instant of `power4.out`, so the timing reads the same.
- **Reverting on complete:** the split lines are fixed-width blocks. Left in place, they keep the old breaks after a resize (the measured layout ran 200 px instead of 132). Reverting returns the original DOM.
- **Putting React's nodes back after every revert (`onRevert`):** SplitText reverts by rewriting the element's `innerHTML`, so the text comes back as new nodes that React doesn't know. Measured without it, in Chromium, Firefox and WebKit: once the reveal ended, a Next `<Link>` inside did a full page reload, an `onClick` inside stopped firing, state updates never reached the text, a structure change crashed React (`removeChild`), and keyboard focus fell back to the page. With it, all five behave.
- **Starting a load reveal on the second frame after the split:** GSAP times a new tween from the last frame it rendered, so anything that holds the main thread before the start counts as elapsed animation. Measured with the main thread blocked 300 ms right after the split: started at once, the first moving frame was already 308–344 ms into the motion, 84–88% of the rise gone, in all three engines. The first frame after the split isn't safe either, because it still has to lay out and paint the split lines. On a page of eight split blocks with Hebrew and emoji (fallback fonts), that frame took about 70 ms: started on it, 4 of 8 loads of a Pages Router production build began 50–73 ms in. Started on the second frame, 8 of 8 began within a frame (5–10 ms). A `delay` counts from that start. A scroll reveal needs none of this, since its ScrollTrigger starts it on a frame.
- **The `!important` in the `<noscript>` rule:** it has to beat the hide rule wherever the framework puts the stylesheet. The Pages Router puts `<noscript>` before the stylesheet, so a rule of equal weight lost there and the text stayed hidden with JavaScript off.

## Failure patterns to avoid
Each was measured in a fresh Next.js 16 project, in Chromium, Firefox and WebKit:
- **`React.cloneElement(children, { ref })`** to attach the ref. It throws "Element type is invalid" and kills the page when the children come from a Server Component, which is the App Router default.
- **Creating the tween or ScrollTrigger after an `await`, outside `contextSafe`.** `useGSAP` can't see it, so nothing is killed on unmount: live ScrollTriggers went from 16 to 176 after ten remounts.
- **Splitting while the unsplit text is showing.** It flashed for about 250 ms before hiding. Keep the CSS hide and the `gsap.set` inside `onSplit`.
- **Splitting before web fonts load,** or with a fixed timeout instead of `document.fonts.ready` and `autoSplit`. The lines break wrongly once the real font arrives.
- **No reduced-motion path.** Users who ask for less motion should get the text with no movement.
- **Letting SplitText's `revert()` stand on its own,** or writing wrapper divs into `innerHTML`: both swap out React's nodes, with the five failures listed under "Why these values".
- **Starting a load reveal the moment it's created:** a busy page cuts off most of its motion.
- **Starting it on the very next frame:** that frame still lays out and paints the split lines. On a heavy page that takes several frames' time, and it counts as motion: a quarter to a third of the rise was gone before the first moving frame, in half the loads.
- **Text that changes while it's split, with no `key`:** a structure change crashed React with `removeChild` in all three engines. With a `key` that changes with the text, the new text lands and reveals.
- **`aria: "auto"` on text that contains links:** the split element gets an `aria-label` and the lines get `aria-hidden`. Measured: the link inside left the accessibility tree for as long as the text was split. With `aria: "none"` it stays reachable.
- **A `<noscript>` rule no stronger than the hide rule:** with JavaScript off, the text stayed hidden in the Pages Router.

## Verify before you finish
Run each check, fix anything that fails, and say which ones you ran:
1. `npx tsc --noEmit` and `npm run build` both succeed.
2. A page that uses `<SplitReveal>` from a Server Component loads with no console errors.
3. On a hard reload, no text shows before its reveal, and the lines rise one after another, from below their masks rather than already partway up.
4. Once the reveal has finished, the element's `innerHTML` is what you wrote: no `.split-line` elements remain.
5. Resize the window after the reveal: the text wraps exactly as plain text would.
6. With reduced motion emulated (DevTools > Rendering > `prefers-reduced-motion: reduce`), the text is simply there, with no movement.
7. Navigate away and back a few times. `ScrollTrigger.getAll().length` doesn't grow, and no lines are nested inside lines. (In development React's Strict Mode mounts each component twice, so the split runs twice on load; a production build splits once.)
8. Text below the fold stays hidden until you scroll to it, then reveals.
9. Put a `<Link>` inside a `SplitReveal`. After the reveal, run `window.__kept = 1` in the console and click it: on the new page `window.__kept` is still 1 (client-side navigation, no full reload). Tab to a link inside text that hasn't revealed yet: after it reveals, the link still has focus.
10. With JavaScript disabled (DevTools > Command Menu, Ctrl+Shift+P > "Disable JavaScript", then reload), the text is visible.
