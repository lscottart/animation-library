---
description: Focus dim. Hover or keyboard-focus one item in a group (project cards, a list of names, a logo wall) and its siblings step back to a quarter opacity and grey, so the one you're on steps forward. The group never flashes when the pointer crosses the gap between two items. Pure CSS with :has(), a Server Component, no JavaScript. For Next.js (App or Pages Router).
argument-hint: "[optional: which group, e.g. 'the project grid on the home page' or 'the client list, no grey']"
model: claude-opus-5-5
effort: max
---

# Focus dim

Build the focus dim in the current project and use it where `$ARGUMENTS` says. If `$ARGUMENTS` is empty, create the component and show it on a grid of four project images and on a list of three names.

## What it looks like
Point at one item in the group and every other item steps back to 25% opacity and greyscale over 0.5s, while the one you're on stays full. Move to another item and the dim follows straight away. Crossing the gap between two items doesn't bring the whole group back for a moment: returning to full waits 80ms, so a normal crossing never shows. Leave the group and everything comes back. Keyboard focus anywhere inside an item does the same. On touch screens nothing dims, because a tap would leave the group stuck dimmed. Under reduced motion it dims at once, with no fade.

## Before you write code
1. **No dependencies.** It's CSS and a Server Component. `:has()` needs Chrome or Edge 105, Safari 15.4 or Firefox 121; older browsers simply don't dim.
2. **The components folder.** Read `tsconfig.json` (or `jsconfig.json`) `compilerOptions.paths` and put both files wherever `@/components/...` resolves: `components/ui/` at the root, or `src/components/ui/`. In a JavaScript project, save it as `FocusDim.jsx` and drop the types.
3. **The router.** In the App Router, the component imports its own CSS. In the Pages Router, import `FocusDim.css` in `pages/_app.tsx` instead and delete the import line from the component.
4. **Every direct child is an item.** Put the cards (or `<li>`s) directly inside `FocusDim`, with no wrapper between them. Use `as="ul"` for a list. Lay the group out with the `className` or `style` you'd give the grid or list anyway.
5. **Options.** `dim` sets the siblings' opacity (0.25 by default; 0.4 suits text). `grayscale={false}` keeps their colour, which is right for type and for a monochrome page.

## Build

### 1. The component: `components/ui/FocusDim.tsx`
A Server Component: no `"use client"`, and it ships no JavaScript.
```tsx
import type { CSSProperties, ElementType, ReactNode } from "react";
import "./FocusDim.css";

/**
 * Hover (or keyboard-focus) one child and its siblings step back. Pure CSS, a Server Component.
 * Every direct child is an item: a card, a list row, a logo, a link.
 */
export default function FocusDim({
  children,
  as: Tag = "div",
  dim = 0.25,
  grayscale = true,
  className,
  style,
}: {
  children: ReactNode;
  as?: ElementType;
  /** the siblings' opacity while one item has focus */
  dim?: number;
  /** also drain the siblings' colour (for images) */
  grayscale?: boolean;
  className?: string;
  style?: CSSProperties;
}) {
  return (
    <Tag
      className={["focus-dim", className].filter(Boolean).join(" ")}
      style={{ "--fd-dim": dim, "--fd-filter": grayscale ? "grayscale(1)" : "none", ...style } as CSSProperties}
    >
      {children}
    </Tag>
  );
}
```

### 2. The CSS: `components/ui/FocusDim.css`
```css
/* Focus dim: hover or keyboard-focus one direct child and its siblings step back.
   Coming back to full waits 80ms, so crossing the gap between two items doesn't flash the whole group;
   stepping back has no wait. */
.focus-dim > * {
  transition:
    opacity 0.5s cubic-bezier(0.2, 0.7, 0.2, 1) 0.08s,
    filter 0.5s cubic-bezier(0.2, 0.7, 0.2, 1) 0.08s;
}
/* only where hover is real: on touch screens a tap would leave the group stuck dimmed */
@media (hover: hover) {
  .focus-dim:has(> :hover) > :not(:hover) {
    opacity: var(--fd-dim, 0.25);
    filter: var(--fd-filter, grayscale(1));
    transition-delay: 0s;
  }
}
/* the keyboard gets the same focus, wherever the focus sits inside the item */
.focus-dim:has(> * :focus-visible, > :focus-visible) > :not(:focus-within) {
  opacity: var(--fd-dim, 0.25);
  filter: var(--fd-filter, grayscale(1));
  transition-delay: 0s;
}
@media (prefers-reduced-motion: reduce) {
  .focus-dim > * {
    transition: none;
  }
}
```

### 3. Use it
```tsx
import FocusDim from "@/components/ui/FocusDim";

<FocusDim className="grid grid-cols-2 gap-6 md:grid-cols-4">
  {projects.map((p) => (
    <a key={p.slug} href={`/houses/${p.slug}`}>
      <img src={p.image} alt={p.title} />
      <span>{p.title}</span>
    </a>
  ))}
</FocusDim>

<FocusDim as="ul" dim={0.4} grayscale={false}>
  <li><a href="/studio/harlan">Harlan House</a></li>
  <li><a href="/studio/meadow">Low Meadow</a></li>
</FocusDim>
```

## Why these values
- **25% and grey:** the siblings recede without vanishing, so the grid's shape still reads. Greyscale drains photographs, so colour belongs to the one in focus. For type, 40% with no grey keeps names legible.
- **0.5s on `cubic-bezier(0.2, 0.7, 0.2, 1)`:** a quick start and a long settle, a step back rather than a fade-out.
- **Stepping back is immediate; coming back waits 80ms:** the pointer spends a frame or two in the gap between items. Without the wait, every crossing flashes the whole group to full.
- **Only where hover is real (`@media (hover: hover)`):** on a phone a tap sets `:hover` and it stays, which would leave the group dimmed until the next tap somewhere else.
- **`:focus-visible` inside an item, `:focus-within` on the item:** the keyboard gets the same focus, wherever the link sits inside the card, and the focus a mouse click leaves behind doesn't count.

## Failure patterns to avoid
Measured on Next.js 16.3.8 and React 19.2.8 in Chromium 153, Firefox 155 and WebKit 26.6 (Playwright 1.63), 2026-10-05:
- **No delay on the way back.** With the 80ms removed, a pointer pausing 40ms in the 24px gap between two tiles flashed the dimmed tiles from 0.25 up to 0.54–0.60 in Chromium, Firefox and WebKit. With the delay, they never rose.
- **Dimming on `:hover` everywhere.** Without the `(hover: hover)` guard, one tap in touch emulation left three of the four tiles dimmed and grey, in Chromium and WebKit. (Firefox has no touch emulation in the test rig.)
- **A wrapper between the group and the items.** The rules target direct children, so a `<div>` around the cards becomes the only item and nothing dims. (A guard, not measured.)

## Verify before you finish
Run each check, fix anything that fails, and say which ones you ran:
1. `npx tsc --noEmit` and `npm run build` both succeed.
2. Point at one item: the others step back; it stays full.
3. Move slowly from one item to the next across the gap: the group doesn't flash back to full on the way.
4. Leave the group: everything comes back.
5. Press Tab through the items: the same focus follows the keyboard.
6. In device emulation (touch), a tap leaves nothing dimmed.
7. With `prefers-reduced-motion: reduce` emulated, it dims at once.
