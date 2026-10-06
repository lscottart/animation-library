---
description: Scroll color fill. A statement fills from grey to ink, character by character, as it scrolls through the reading band, at the reader's own pace. Characters are split on the server in React (no DOM rewriting), grapheme-safe, words never break. For Next.js (App or Pages Router) + GSAP ScrollTrigger.
argument-hint: "[optional: which text, e.g. 'the studio statement on the about page']"
model: claude-opus-5-5
effort: max
---

# Scroll color fill

Build the scroll color fill in the current project and use it where `$ARGUMENTS` says. If `$ARGUMENTS` is empty, create the component and show it on a one- or two-sentence statement set large, with room to scroll past it.

## What it looks like
A large statement starts light grey. As it scrolls up through the reading band (from its top at 78% of the screen to its bottom at 42%), the characters turn ink one after another in reading order. The fill sweeps along each line and down the paragraph like a highlighter that follows your eyes. It's tied to the scroll position, so stopping stops it and scrolling back unfills it. Each character fills as one piece, including accented letters, emoji and flags, and a word never breaks across two lines. With reduced motion the text is simply ink.

## Before you write code
1. **GSAP.** Check `package.json` for `gsap` (3.12 or later) and `@gsap/react`. If either is missing, run `npm install gsap @gsap/react`. ScrollTrigger ships inside `gsap`. No SplitText needed.
2. **The components folder.** Read `tsconfig.json` (or `jsconfig.json`) `compilerOptions.paths` and put both files wherever `@/components/...` resolves: `components/ui/` at the root, or `src/components/ui/`. In a JavaScript project, save it as `ScrollColorFill.jsx` and drop the types.
3. **The router.** In the App Router, the component imports its own CSS. In the Pages Router, import `ScrollColorFill.css` in `pages/_app.tsx` instead and delete the import line from the component.
4. **Plain text only.** The text must be a string: a statement, a heading, a pull quote. It's for display text, a sentence or a short paragraph, not for body copy or anything with links inside.
5. **Colours.** Pass `from` (the unfilled grey) and `to` (the ink) as colour values. The defaults are `#b4b6b8` and `#17191a`, for a light page. On a dark page, use a dim grey for `from` and the page's text colour for `to`.

## Build

### 1. The component: `components/ui/ScrollColorFill.tsx`
```tsx
"use client";

import { useRef, type CSSProperties, type ElementType } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useGSAP } from "@gsap/react";
import "./ScrollColorFill.css";

gsap.registerPlugin(ScrollTrigger, useGSAP);

// One span per user-perceived character, so an emoji or an accented letter fills as one piece.
// Intl.Segmenter is in Node and in every current browser, so the server and the browser split alike.
function characters(text: string): string[] {
  if (typeof Intl !== "undefined" && "Segmenter" in Intl) {
    return Array.from(new Intl.Segmenter(undefined, { granularity: "grapheme" }).segment(text), (s) => s.segment);
  }
  return Array.from(text);
}

type Props = {
  children: string;
  /** the element to render: p, h2, blockquote... */
  as?: ElementType;
  /** the colour before the fill, and the colour it fills to */
  from?: string;
  to?: string;
  /** where the fill starts and ends, as ScrollTrigger positions */
  start?: string;
  end?: string;
  className?: string;
  style?: CSSProperties;
};

export default function ScrollColorFill({
  children,
  as: Tag = "p",
  from = "#b4b6b8",
  to = "#17191a",
  start = "top 78%",
  end = "bottom 42%",
  className,
  style,
}: Props) {
  const root = useRef<HTMLElement>(null);
  // Split on the server, in React: React owns every span, so nothing rewrites the DOM behind its back.
  // Whitespace stays plain text between the words, so lines break exactly as they would without the effect.
  const parts = children.split(/(\s+)/).filter((w) => w !== "").map((w) => (/^\s+$/.test(w) ? w : characters(w)));

  useGSAP(
    () => {
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
      const chars = root.current!.querySelectorAll(".scf__ch");
      gsap.fromTo(chars, { color: from }, { color: to, ease: "none", stagger: 0.05, scrollTrigger: { trigger: root.current!, start, end, scrub: 0.4 } });
    },
    { scope: root, dependencies: [children, from, to, start, end], revertOnUpdate: true },
  );

  return (
    <Tag ref={root} className={["scf", className].filter(Boolean).join(" ")} style={{ "--scf-from": from, "--scf-to": to, ...style } as CSSProperties}>
      {parts.map((part, pi) =>
        typeof part === "string" ? (
          part
        ) : (
          // a word never breaks across lines: its letters stay together
          <span key={pi} className="scf__word">
            {part.map((ch, ci) => (
              <span key={ci} className="scf__ch">
                {ch}
              </span>
            ))}
          </span>
        ),
      )}
    </Tag>
  );
}
```

### 2. The CSS: `components/ui/ScrollColorFill.css`
```css
/* Scroll color fill: each character starts in the "from" colour and is filled to "to" as the text scrolls
   through the reading band. GSAP drives the colours; this file sets the starting state and the fallbacks. */
.scf__word {
  white-space: nowrap; /* a word's letters never split across two lines */
}
.scf__ch {
  color: var(--scf-from);
}
/* reduced motion: no fill, the text simply reads in its final colour */
@media (prefers-reduced-motion: reduce) {
  .scf__ch {
    color: var(--scf-to);
  }
}
```

### 3. Use it
```tsx
import ScrollColorFill from "@/components/ui/ScrollColorFill";

<ScrollColorFill className="statement">
  Before we draw anything, we stand on the land at dusk, mark where the last sun falls, and design every room to answer it.
</ScrollColorFill>

<ScrollColorFill as="h2" from="#3a3c3e" to="#f2f2f2">
  Every photograph here was taken in that hour.
</ScrollColorFill>
```
Set the type size and measure on the element (`className` or `style`): it works best large (32px and up) and narrow (about 20 characters a line).

## Why these values
- **From 78% to 42% of the screen:** the fill begins as the text enters the lower part of the view and completes just above the middle, where people read. The whole statement is ink before it leaves.
- **Per character, scrubbed (`ease: "none"`, `scrub: 0.4`):** the fill is a position, not a timed animation. It goes as fast as the reader scrolls, and the 0.4s smoothing keeps a wheel flick from stepping.
- **A stagger of 0.05 across the characters:** inside a scrubbed timeline, that spreads the fill so a few characters are mid-fill at any moment, which gives a soft leading edge instead of a hard cut.
- **Splitting in React, on the server:** the text is in the server HTML, React owns every span, and changing the text later just re-renders.

## Failure patterns to avoid
Measured on Next.js 16.3.8 with GSAP 3.15, in Chromium, Firefox and WebKit, 2026-10-05:
- **Splitting with `Array.from` or `.split("")`.** The suite's grapheme check failed in all three engines. A decomposed é split into an "e" and a floating accent, the ZWJ emoji into four pieces and the flag into two letters. `Intl.Segmenter` keeps each one whole.
- **Expecting the character spans to break words.** They don't: inline spans add no line-break opportunities, so with the no-wrap wrapper removed, words still wrapped whole in the test. The wrapper is there for pages that set `overflow-wrap: anywhere` or `word-break: break-all` (Tailwind's `break-all`), which would otherwise split a statement mid-word. Not measured; a guard.
- **Splitting the DOM with a library that rewrites it** (SplitText and the like) inside a React component. The split-text-line-reveal skill in this library measured React losing its DOM nodes after a revert. Here React renders the characters itself.

## Verify before you finish
Run each check, fix anything that fails, and say which ones you ran:
1. `npx tsc --noEmit` and `npm run build` both succeed.
2. View the page source (or `curl` it): the whole sentence is in the HTML. In the browser, the element's `innerText` is the sentence itself.
3. Scroll the statement up slowly: it fills in reading order and is all ink before it passes the middle of the screen. Scroll back down: it unfills.
4. A word never breaks across two lines, and accented letters, emoji and flags fill as single characters.
5. If the text can change, change it while the page is open: the new text renders and still fills, with no console errors.
6. With `prefers-reduced-motion: reduce` emulated, the text is ink and doesn't change as you scroll.
