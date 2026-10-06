---
description: Travelling indicator. One highlight travels between a nav's items (or a set of filters, or a toolbar's icon buttons) and resizes to each, instead of every item owning its own hover. An ink block with the text inverting inside it, a hairline underline, or one tooltip that slides between buttons. Right on first paint, keyboard-aware. For Next.js (App or Pages Router) + GSAP.
argument-hint: "[optional: where and which variant, e.g. 'the header nav, block' or 'the project filters, underline' or 'the image toolbar, tooltip']"
model: claude-opus-5-5
effort: max
---

# Travelling indicator

Build the travelling indicator in the current project and use it where `$ARGUMENTS` says. If `$ARGUMENTS` is empty, create the component and show a five-item nav in the block variant, a filter row in the underline variant, and a four-button toolbar with the tooltip.

## What it looks like
- **Block (`TravellingNav`, the default):** the current page sits in an ink block, its label in paper colour. Point at another item and the block slides there in 0.5s on expo.out, resizing to the new item's width. The text turns paper exactly where the block covers it, so mid-slide a word can be half ink, half paper. Leave the nav and the block slides back to the current page. Click an item and it becomes current. If no item is current, the block is hidden; it appears on the first item you point at (it doesn't slide in from nowhere) and fades when you leave.
- **Underline (`variant="underline"`):** the same, with a 1px hairline under the item instead of a block.
- **Tooltip (`TravellingTooltip`):** a toolbar of icon buttons with one label above them. The first hover makes the label rise into place; moving to another button slides the label across and resizes it to the new word, without fading out and back in. It hides 0.12s after the pointer leaves the toolbar, so crossing the gap between two buttons doesn't flicker it.

Keyboard focus moves the highlight just like hover, but only focus from the keyboard, not the focus a mouse click leaves behind. A tap on a touch screen just follows the link. Under reduced motion the highlight jumps instead of sliding. Before JavaScript runs, plain CSS already marks the current page, so the first paint is right.

## Before you write code
1. **GSAP.** Check `package.json` for `gsap` (3.12 or later). If it's missing, run `npm install gsap`. No plugins are needed.
2. **The components folder.** Read `tsconfig.json` (or `jsconfig.json`) `compilerOptions.paths` and put both files wherever `@/components/...` resolves: `components/ui/` at the root, or `src/components/ui/`. In a JavaScript project, save it as `TravellingIndicator.jsx` and drop the types.
3. **The router.** In the App Router, the component imports its own CSS. In the Pages Router, import `TravellingIndicator.css` in `pages/_app.tsx` instead and delete the import line from the component.
4. **The current page.** `current` is the `href` of the item to highlight at rest. For a site nav, pass the pathname: `usePathname()` from `next/navigation` in the App Router (inside a Client Component), or `useRouter().pathname` from `next/router` in the Pages Router. For filters, keep the selected filter in state and pass it, with `onSelect` to hear clicks. `onSelect` is a function, so the parent must be a Client Component.
5. **Colours and type.** The ink and paper colours are two CSS variables, `--ti-ink` and `--ti-paper`, set on `.tn` and `.tt`. Override them in the project's CSS to match the palette. The items inherit the font; size them through the parent.

## Build

### 1. The component: `components/ui/TravellingIndicator.tsx`
It exports two Client Components: `TravellingNav` (block or underline) and `TravellingTooltip`.
```tsx
"use client";

import Link from "next/link";
import { useEffect, useLayoutEffect, useRef, useState, type FocusEvent as ReactFocusEvent, type PointerEvent as ReactPointerEvent, type ReactNode } from "react";
import gsap from "gsap";
import "./TravellingIndicator.css";

// useLayoutEffect warns during server rendering; this runs it only in the browser.
const useIsoLayoutEffect = typeof window !== "undefined" ? useLayoutEffect : useEffect;
const still = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const MOVE = { duration: 0.5, ease: "expo.out" } as const;

type Box = { l: number; t: number; w: number; h: number };
const boxIn = (outer: HTMLElement, el: HTMLElement): Box => {
  const o = outer.getBoundingClientRect(), r = el.getBoundingClientRect();
  return { l: r.left - o.left, t: r.top - o.top, w: r.width, h: r.height };
};

export type TravelItem = { label: string; href: string };

/**
 * A nav (or a set of filters) with one highlight that travels between the items and resizes to each,
 * instead of every item owning its own hover.
 * block:     an ink block; the text inside it turns paper colour (a second copy of the row, clipped to the block)
 * underline: a hairline under the item
 */
export function TravellingNav({
  items,
  current,
  variant = "block",
  label = "Main",
  onSelect,
}: {
  items: TravelItem[];
  /** the href of the current page; that item is highlighted at rest */
  current?: string;
  variant?: "block" | "underline";
  label?: string;
  onSelect?: (href: string) => void;
}) {
  const root = useRef<HTMLElement>(null);
  const mark = useRef<HTMLDivElement>(null);
  const links = useRef<(HTMLAnchorElement | null)[]>([]);
  const [picked, setPicked] = useState<string | undefined>(current);
  const active = items.findIndex((i) => i.href === (picked ?? current));
  const target = useRef<number>(active);
  const [prevCurrent, setPrevCurrent] = useState(current);
  if (current !== prevCurrent) {
    // a new page: follow it
    setPrevCurrent(current);
    setPicked(current);
  }

  // Move the highlight to item k (or away, for -1). Instant the first time and on resize.
  const moveTo = (k: number, instant = false) => {
    target.current = k;
    const el = root.current, m = mark.current;
    if (!el || !m) return;
    const d = instant || still() ? 0 : MOVE.duration;
    const a = k >= 0 ? links.current[k] : null;
    if (variant === "block") {
      if (!a) {
        gsap.to(m, { opacity: 0, duration: d * 0.6, ease: "power2.out", overwrite: true });
        return;
      }
      const b = boxIn(el, a), W = el.clientWidth, H = el.clientHeight;
      const wasHidden = Number(gsap.getProperty(m, "opacity")) < 0.01;
      const clip = `inset(${b.t}px ${W - b.l - b.w}px ${H - b.t - b.h}px ${b.l}px)`;
      if (wasHidden) gsap.set(m, { clipPath: clip });
      gsap.to(m, { clipPath: clip, opacity: 1, duration: d, ease: MOVE.ease, overwrite: true });
    } else {
      if (!a) {
        gsap.to(m, { opacity: 0, duration: d * 0.6, ease: "power2.out", overwrite: true });
        return;
      }
      const b = boxIn(el, a);
      const wasHidden = Number(gsap.getProperty(m, "opacity")) < 0.01;
      if (wasHidden) gsap.set(m, { x: b.l, width: b.w });
      gsap.to(m, { x: b.l, width: b.w, opacity: 1, duration: d, ease: MOVE.ease, overwrite: true });
    }
  };

  // Place it at the active item before the first paint (instantly), and travel when the active item changes later.
  const placed = useRef<string | null>(null);
  useIsoLayoutEffect(() => {
    moveTo(active, placed.current !== variant);
    placed.current = variant;
    root.current?.setAttribute("data-ready", "");
  }, [active, variant]);
  // ...and snap back into place whenever the layout or the fonts change
  useEffect(() => {
    const el = root.current!;
    const again = () => moveTo(target.current, true);
    const ro = new ResizeObserver(again);
    ro.observe(el);
    document.fonts?.ready.then(again);
    return () => ro.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [variant]);

  const enter = (k: number) => (e: ReactPointerEvent) => {
    if (e.pointerType !== "touch") moveTo(k); // a tap just follows the link
  };
  const row = (copy: boolean) =>
    items.map((it, k) =>
      copy ? (
        <span key={it.href} className="tn__item">
          {it.label}
        </span>
      ) : (
        <Link
          key={it.href}
          ref={(el) => {
            links.current[k] = el;
          }}
          href={it.href}
          className="tn__item"
          aria-current={k === active ? "page" : undefined}
          onPointerEnter={enter(k)}
          onFocus={(e) => e.currentTarget.matches(":focus-visible") && moveTo(k)}
          onClick={() => {
            setPicked(it.href);
            onSelect?.(it.href);
          }}
        >
          {it.label}
        </Link>
      ),
    );

  return (
    <nav
      ref={root}
      aria-label={label}
      className={`tn tn--${variant}`}
      onPointerLeave={(e) => e.pointerType !== "touch" && moveTo(active)}
      onBlur={(e) => !e.currentTarget.contains(e.relatedTarget as Node) && moveTo(active)}
    >
      <div className="tn__row">{row(false)}</div>
      {variant === "block" ? (
        <div ref={mark} className="tn__block" aria-hidden="true">
          <div className="tn__row">{row(true)}</div>
        </div>
      ) : (
        <div ref={mark} className="tn__line" aria-hidden="true" />
      )}
    </nav>
  );
}

export type ToolItem = { label: string; icon: ReactNode; onClick?: () => void; href?: string };

/** A toolbar with one tooltip that travels between the buttons and resizes to each label. */
export function TravellingTooltip({ items, label = "Tools" }: { items: ToolItem[]; label?: string }) {
  const root = useRef<HTMLDivElement>(null);
  const tip = useRef<HTMLDivElement>(null);
  const tipText = useRef<HTMLSpanElement>(null);
  const measure = useRef<HTMLSpanElement>(null);
  const shown = useRef(false);
  const hide = useRef<gsap.core.Tween | null>(null);

  const show = (k: number, el: HTMLElement) => {
    hide.current?.kill();
    const o = root.current!, t = tip.current!;
    measure.current!.textContent = items[k].label;
    const w = measure.current!.offsetWidth + 20;
    const b = boxIn(o, el);
    const x = b.l + b.w / 2 - w / 2;
    tipText.current!.textContent = items[k].label;
    if (!shown.current || still()) {
      // first appearance: in place, no travel
      gsap.set(t, { x, width: w });
      gsap.fromTo(t, { opacity: 0, y: 4 }, { opacity: 1, y: 0, duration: still() ? 0 : 0.2, ease: "power3.out", overwrite: true });
      shown.current = true;
    } else {
      gsap.to(t, { x, width: w, opacity: 1, y: 0, duration: MOVE.duration, ease: MOVE.ease, overwrite: true });
    }
  };
  const leave = () => {
    hide.current = gsap.to(tip.current, {
      opacity: 0,
      y: 4,
      duration: still() ? 0 : 0.18,
      delay: 0.12, // crossing the gap between two buttons doesn't hide it
      ease: "power2.in",
      overwrite: true,
      onComplete: () => {
        shown.current = false;
      },
    });
  };

  return (
    <div ref={root} role="toolbar" aria-label={label} className="tt" onPointerLeave={(e) => e.pointerType !== "touch" && leave()}>
      <div ref={tip} className="tt__tip" aria-hidden="true">
        <span ref={tipText} />
      </div>
      <span ref={measure} className="tt__tip tt__measure" aria-hidden="true" />
      {items.map((it, k) => {
        const props = {
          className: "tt__btn",
          "aria-label": it.label,
          onPointerEnter: (e: ReactPointerEvent<HTMLElement>) => e.pointerType !== "touch" && show(k, e.currentTarget),
          onFocus: (e: ReactFocusEvent<HTMLElement>) => e.currentTarget.matches(":focus-visible") && show(k, e.currentTarget),
          onBlur: leave,
        };
        return it.href ? (
          <Link key={it.label} href={it.href} {...props}>
            {it.icon}
          </Link>
        ) : (
          <button key={it.label} type="button" onClick={it.onClick} {...props}>
            {it.icon}
          </button>
        );
      })}
    </div>
  );
}
```

### 2. The CSS: `components/ui/TravellingIndicator.css`
```css
/* Travelling indicator. Colours come from two variables; set them on .tn / .tt or :root. */
.tn,
.tt {
  --ti-ink: #17191a;
  --ti-paper: #f2f2f2;
}
.tn {
  position: relative;
  display: inline-block;
}
.tn__row {
  display: flex;
}
.tn__item {
  display: block;
  padding: 0.45em 0.85em;
  color: inherit;
  text-decoration: none;
  white-space: nowrap;
}
.tn__item:focus-visible {
  outline: 1px solid currentColor;
  outline-offset: -3px;
}
/* block: a second copy of the row, paper on ink, clipped to the highlight. JS moves the clip. */
.tn__block {
  position: absolute;
  inset: 0;
  background: var(--ti-ink);
  color: var(--ti-paper);
  pointer-events: none;
  opacity: 0;
  clip-path: inset(0 100% 0 0);
}
/* before JavaScript has placed the highlight, the current page is marked with plain CSS, so the first paint is right */
.tn--block:not([data-ready]) .tn__row > [aria-current="page"] {
  background: var(--ti-ink);
  color: var(--ti-paper);
}
/* underline: a hairline under the item; JS sets its x and width */
.tn--underline .tn__item {
  padding-bottom: 0.6em;
}
.tn__line {
  position: absolute;
  left: 0;
  bottom: 0;
  width: 0;
  height: 1px;
  background: var(--ti-ink);
  opacity: 0;
  pointer-events: none;
}
.tn--underline:not([data-ready]) .tn__row > [aria-current="page"] {
  box-shadow: inset 0 -1px 0 var(--ti-ink);
}

/* tooltip toolbar */
.tt {
  position: relative;
  display: inline-flex;
  gap: 4px;
  padding-top: 46px;
}
.tt__btn {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  padding: 0;
  border: 1px solid color-mix(in srgb, var(--ti-ink) 16%, transparent);
  background: transparent;
  color: var(--ti-ink);
  cursor: pointer;
}
.tt__btn:focus-visible {
  outline: 1px solid var(--ti-ink);
  outline-offset: 2px;
}
.tt__tip {
  position: absolute;
  top: 0;
  left: 0;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  white-space: nowrap;
  font-size: 13px;
  background: var(--ti-ink);
  color: var(--ti-paper);
  pointer-events: none;
  opacity: 0;
}
/* an invisible twin the component measures labels with */
.tt__measure {
  visibility: hidden;
  width: auto;
  padding: 0;
}
```

### 3. Use it
A site nav, App Router (`components/SiteNav.tsx`):
```tsx
"use client";

import { usePathname } from "next/navigation";
import { TravellingNav } from "@/components/ui/TravellingIndicator";

const NAV = [
  { label: "Houses", href: "/houses" },
  { label: "Studio", href: "/studio" },
  { label: "Journal", href: "/journal" },
  { label: "Contact", href: "/contact" },
];

export default function SiteNav() {
  return <TravellingNav items={NAV} current={usePathname()} />;
}
```
In the Pages Router, the same with `import { useRouter } from "next/router"` and `current={useRouter().pathname}`.

Filters, underline:
```tsx
"use client";

import { useState } from "react";
import { TravellingNav } from "@/components/ui/TravellingIndicator";

const TYPES = ["All", "Houses", "Interiors", "Landscape"].map((t) => ({ label: t, href: `#${t.toLowerCase()}` }));

export default function Filters() {
  const [type, setType] = useState("#all");
  return <TravellingNav items={TYPES} current={type} variant="underline" label="Filter projects" onSelect={setType} />;
}
```

A toolbar (each icon needs a label; it's the button's accessible name and the tooltip's text):
```tsx
import { TravellingTooltip } from "@/components/ui/TravellingIndicator";

<TravellingTooltip
  label="Image tools"
  items={[
    { label: "Share", icon: <ShareIcon />, onClick: share },
    { label: "Download", icon: <DownloadIcon />, href: "/press/harlan-house.zip" },
  ]}
/>
```

## Why these values
- **One highlight that travels, not a hover on every item:** the eye follows one object across the row, which reads as a considered system rather than a set of effects. Seen on recent Site of the Day winners (Aspen Search's nav pill, LXL's underline) and in rauno's free Spatial Tooltip and Exclusion Tabs; this is an independent build of the general pattern, with square corners and a clipped text inversion.
- **0.5s on expo.out:** it leaves fast and settles long, so the block arrives decisively and never looks like it's sliding on ice. This is a choice, not measured from a source.
- **A second copy of the row, clipped to the block:** the paper text is exactly where the block is, even mid-slide when the block straddles two words. One `clip-path` tween drives both the shape and the inversion. A blend mode would tie the text colour to whatever is behind it.
- **Appearing in place when nothing was highlighted:** a block that slides in from the last place it was, or from the left edge, reads like a glitch.
- **The 0.12s hide delay on the tooltip:** crossing the 4px gap between buttons takes a frame or two; without the delay, the label would start to fade on every crossing.

## Failure patterns to avoid
Measured on Next.js 16.3.8 and React 19.2.8 in Chromium 153, Firefox 155 and WebKit 26.6 (Playwright 1.63), 2026-10-05:
- **Tweening the block in when nothing was highlighted.** With the in-place `gsap.set` removed, the block grew or slid in from its last position instead of appearing on the item. The suite's "appears on the item" check failed in Chromium, Firefox and WebKit. Keep the set.
- **Leaving the first paint to JavaScript.** With the `:not([data-ready])` rule removed, the current page had no highlight before JavaScript ran (its background was transparent) in all three engines. On a slow connection, that's what visitors see first.
- **Measuring before the web font has loaded.** The block would be sized to the fallback font. The component measures again on `document.fonts.ready` and whenever the nav resizes. (A guard, not measured.)

## Verify before you finish
Run each check, fix anything that fails, and say which ones you ran:
1. `npx tsc --noEmit` and `npm run build` both succeed.
2. With JavaScript disabled (or in the page source), the current page is already highlighted.
3. Point at another item: the block slides there and resizes, and the text inside it turns paper. Leave: it returns to the current page.
4. With no current item, the highlight appears on the first item you point at, without sliding in.
5. Press Tab into the nav (use the real Tab key; in Firefox, a scripted `.focus()` after a mouse click doesn't count as keyboard focus): the highlight follows focus, and returns when focus leaves.
6. The toolbar: the label appears over the first button, slides to the next without fading, and hides when you leave.
7. With `prefers-reduced-motion: reduce` emulated, the highlight jumps instead of sliding.
