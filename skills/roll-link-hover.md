---
description: Roll link hover. On hover a link's letters roll up one line, a dimmer copy rising from below, in a 15ms left-to-right wave. Pure CSS, server-rendered text, one accessible name, no letter limit; for Next.js (any router).
argument-hint: "[optional: where to use it, e.g. 'the header nav links in components/Header.tsx']"
model: claude-opus-5-5
effort: max
---

# Roll link hover

Build the roll link in the current project and use it where `$ARGUMENTS` says. If `$ARGUMENTS` is empty, create the component and show it on a short nav (Work, About, Contact) plus one multi-word link.

## What it looks like
At rest the link reads normally. On hover, each letter slides up exactly one line and out of a one-line window, while a copy of the same letter, at half opacity, rises from below to take its place. The letters start 15ms apart, left to right, so the label rolls as a quick wave rather than a block. Each letter's move is 0.3s on `cubic-bezier(0.76, 0, 0.24, 1)`: it accelerates hard, then brakes hard, so the roll reads crisp and mechanical. Moving off rolls it back the same way. Keyboard focus rolls it too, a tap on a touch screen leaves nothing stuck, and with reduced motion the link underlines instead.

## Before you write code
1. **The components folder.** Read `tsconfig.json` (or `jsconfig.json`) `compilerOptions.paths` and put the files wherever `@/components/...` resolves: `components/ui/` at the root, or `src/components/ui/`. In a JavaScript project, save the component as `RollLink.jsx` and drop the types.
2. **The router.** In the App Router, the component imports its own CSS. In the Pages Router, import `RollLink.css` in `pages/_app.tsx` instead and delete the import line from the component.
3. **Plain links only.** The label must be a string. For a link that holds an icon or other markup, keep the icon outside `RollLink`, next to it.

## Build

### 1. The component: `components/ui/RollLink.tsx`
It renders on the server and needs no `"use client"`. It works in Server and Client Components alike.
```tsx
import Link from "next/link";
import type { ComponentProps, CSSProperties } from "react";
import "./RollLink.css";

type RollLinkProps = Omit<ComponentProps<typeof Link>, "children"> & { children: string };

// One span per user-perceived character, so an emoji or an accented letter rolls as one piece.
// Intl.Segmenter is in Node and in every current browser, so the server and the browser split alike.
function characters(text: string): string[] {
  if (typeof Intl !== "undefined" && "Segmenter" in Intl) {
    return Array.from(new Intl.Segmenter(undefined, { granularity: "grapheme" }).segment(text), (s) => s.segment);
  }
  return Array.from(text);
}

export default function RollLink({ children, className, ...rest }: RollLinkProps) {
  return (
    <Link aria-label={children} {...rest} className={["roll-link", className].filter(Boolean).join(" ")}>
      <span className="roll-window">
        {characters(children).map((ch, i) => (
          <span key={i} className="roll-letter" data-ch={ch} style={{ "--i": i } as CSSProperties}>
            {ch}
          </span>
        ))}
      </span>
    </Link>
  );
}
```

### 2. The CSS: `components/ui/RollLink.css`
```css
.roll-link {
  display: inline-block;
  color: inherit;
  text-decoration: none;
}
/* the one-line window that hides the copy below */
.roll-window {
  display: inline-block; /* inline, not flex: flex items would put each letter on its own line in copied text */
  overflow: hidden;
  height: 1.2em;
  line-height: 1.2em;
  white-space: pre; /* keeps the spaces of a multi-word label */
  vertical-align: top;
}
.roll-letter {
  position: relative;
  display: inline-block; /* transforms need a box */
  transition: transform 0.3s cubic-bezier(0.76, 0, 0.24, 1);
  transition-delay: calc(var(--i) * 15ms); /* the wave, for a label of any length */
}
/* the copy that rolls in: generated content, so the text is in the DOM once */
.roll-letter::after {
  content: attr(data-ch);
  content: attr(data-ch) / ""; /* where supported, kept out of the accessible name */
  position: absolute;
  left: 0;
  top: 100%;
  opacity: 0.5;
}
@media (hover: hover) {
  .roll-link:hover .roll-letter {
    transform: translateY(-100%);
  }
}
.roll-link:focus-visible .roll-letter {
  transform: translateY(-100%);
}
@media (prefers-reduced-motion: reduce) {
  .roll-letter {
    transition: none;
  }
  .roll-link:hover .roll-letter,
  .roll-link:focus-visible .roll-letter {
    transform: none;
  }
  .roll-link:hover,
  .roll-link:focus-visible {
    text-decoration: underline;
    text-underline-offset: 0.2em;
  }
}
```

### 3. Use it
```tsx
import RollLink from "@/components/ui/RollLink";

<nav style={{ display: "flex", gap: 24 }}>
  <RollLink href="/work">Work</RollLink>
  <RollLink href="/about">About</RollLink>
  <RollLink href="/contact">Contact</RollLink>
</nav>

<RollLink href="https://www.instagram.com/yourname" target="_blank" rel="noopener noreferrer">
  Instagram
</RollLink>
```
Any `Link` prop passes through: `prefetch`, `target`, `onClick`, `className`. The link gets `aria-label` set to its label, which you can override. Outside Next.js, swap `Link` for `<a>`; nothing else changes.

## Why these values
- **`cubic-bezier(0.76, 0, 0.24, 1)` over 0.3s:** a hard ease-in-out. The letter barely moves, flies through the middle, then stops dead. That's what makes the swap read as a mechanical roll. A plain `ease-in-out` reads soft.
- **15ms per letter:** the wave is felt rather than counted. At 30ms it turns into a visible sequence, and at 5ms it collapses into a block. The delay comes from each letter's index (`--i`), so a 40-character label waves all the way through.
- **A half-opacity copy:** the incoming letters are a different layer from the outgoing ones, so the roll has a direction. At full opacity the swap is invisible.
- **A `1.2em` window with `1.2em` line-height:** the window is exactly one line, so the copy is fully hidden at rest and each move travels exactly one line. If the face's descenders or accents get clipped, raise both values together, for example to `1.3em`.
- **One DOM copy, a CSS `::after` second copy:** the text is in the page once, so search engines, translation and copy-paste see "About". The link's `aria-label` gives screen readers one clean name, even where `content: … / ""` isn't supported.

## Failure patterns to avoid
Each was measured in a fresh Next.js 16 project:
- **Building the letters in `useLayoutEffect` with `innerHTML`.** The server HTML held empty links, so the label was missing before hydration and without JavaScript.
- **Two DOM copies of the text with no `aria-label`:** screen readers read "About About".
- **Per-letter `:nth-child` delays up to a fixed count:** letters past the 20th all moved at once, so the wave broke on long labels.
- **`:hover` without `@media (hover: hover)`:** on a phone, a tap left the label stuck rolled.
- **No `:focus-visible` state, and no reduced-motion path.**
- **Splitting with `.split("")` or `for…of`:** `for…of` cut "Über café 👩🏽‍💻 🇨🇭" (with the é typed as e plus an accent mark) into 18 pieces instead of 13: the accent came off its e, and the emoji and the flag broke apart. `.split("")` made 23. `Intl.Segmenter` keeps each one whole.
- **A flex or grid window (`display: inline-flex`).** Its letters become block-level items, so copied text and `innerText` came out one letter per line ("A b o u t") in testing. Keep the window `inline-block` and the letters `inline-block`.

## Verify before you finish
Run each check, fix anything that fails, and say which ones you ran:
1. `npx tsc --noEmit` and `npm run build` both succeed.
2. View the page source (or `curl` the page): every roll link's label is in the HTML. In the browser, the link's `innerText` is the label itself, "About", not one letter per line.
3. The accessibility tree names each link once ("About"), not twice.
4. Hover: every letter rolls up in a left-to-right wave, including in a label longer than 20 characters, and moving off rolls it back.
5. Tab to a link: it rolls. In device emulation (touch), a tap leaves nothing rolled.
6. With `prefers-reduced-motion: reduce` emulated, there's no rolling, and the link underlines on hover.
7. At rest, no part of the copy shows under the label, and nothing is clipped. Check a label with descenders, like "Typography".
