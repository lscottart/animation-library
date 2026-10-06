---
description: List hover sliding fill. A link list whose hover fill slides from row to row like one bar (Obys DES project index). Pure CSS, server component, works with or without Tailwind (v3 or v4), keyboard and touch safe.
argument-hint: "[optional: where to use it and the items, e.g. 'socials in the footer: X, Instagram, LinkedIn']"
model: claude-opus-5-5
effort: max
---

# List hover sliding fill

Build the sliding-fill link list in the current project and use it where `$ARGUMENTS` says. If `$ARGUMENTS` is empty, create the component and show it with three example rows.

## What it looks like
A vertical list of links, each row closed off by a 1px rule. Hover a row and a solid fill grows down from its top edge while the text turns the page colour. The label slides 15px right while the arrow slides 15px left, so the two push apart. Move the pointer down to the next row and the first row's fill shrinks toward its bottom edge while the next row's fill grows from its top edge, at the same moment. The two read as one bar sliding down the list. The effect is pure CSS: no JavaScript and no GSAP. The trick is that `transform-origin` switches instantly (it isn't transitioned) while the `scaleY` transform eases over 500ms.

## Before you write code
1. **The components folder.** Read `tsconfig.json` (or `jsconfig.json`) `compilerOptions.paths` and put the files wherever `@/components/...` resolves: `components/ui/` at the root, or `src/components/ui/`. In a JavaScript project, save the component as `SlidingFillList.jsx` and drop the types.
2. **The router.** In the App Router (`app/`), the component imports its own CSS file. In the Pages Router, import `SlidingFillList.css` once in `pages/_app.tsx` instead, since Pages only allows global CSS there, and delete the import line from the component.
3. **Colours.** Find the page's text colour and background colour, from the global CSS or the Tailwind theme. The list reads both from two CSS variables: `--sfl-ink` (the rules, the fill and the idle text) and `--sfl-paper` (the background, which also becomes the hovered text). Set them on the list, a section or `:root`, as plain colour values or `var(--…)` references to the project's tokens. Don't use Tailwind colour utilities for these: on Tailwind v4 a `tailwind.config.js` theme is ignored, so the classes don't exist.

## Build

### 1. The component: `components/ui/SlidingFillList.tsx`
```tsx
import Link from "next/link";
import "./SlidingFillList.css";

export type SlidingFillItem = {
  label: string;
  href: string;
  /** opens in a new tab (use for off-site links) */
  external?: boolean;
};

export default function SlidingFillList({ items, className = "" }: { items: SlidingFillItem[]; className?: string }) {
  return (
    <ul className={`sfl ${className}`.trim()}>
      {items.map((item, i) => {
        const inner = (
          <>
            <span className="sfl-fill" aria-hidden="true" />
            <span className="sfl-label">{item.label}</span>
            <span className="sfl-icon" aria-hidden="true">
              <svg width="12" height="12" viewBox="0 0 8 8" fill="none">
                <path d="M1 7.5L7.5 1M7.5 1V6.5M7.5 1H1.5" stroke="currentColor" />
              </svg>
            </span>
          </>
        );
        return (
          <li key={`${item.href}-${i}`}>
            {item.external ? (
              <a className="sfl-row" href={item.href} target="_blank" rel="noopener noreferrer">
                {inner}
              </a>
            ) : (
              <Link className="sfl-row" href={item.href}>
                {inner}
              </Link>
            )}
          </li>
        );
      })}
    </ul>
  );
}
```

### 2. The CSS: `components/ui/SlidingFillList.css`
```css
/* Colours come from two variables set on the list or any ancestor (the page, a section, a class):
   --sfl-ink: the rules, the fill and the idle text, so the page's text colour;
   --sfl-paper: the page's background, which is also the hovered text.
   The component only reads them, with fallbacks, so whatever sets them wins regardless of CSS order. */
.sfl {
  --sfl-ease: cubic-bezier(0.4, 0, 0.2, 1);
  list-style: none;
  margin: 0;
  padding: 0;
  border-top: 1px solid var(--sfl-ink, #17191a);
}
.sfl-row {
  position: relative;
  isolation: isolate; /* the fill's z-index -1 stays inside the row instead of sinking behind the section's background */
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 28px 0;
  line-height: 1;
  color: var(--sfl-ink, #17191a);
  text-decoration: none;
  border-bottom: 1px solid currentColor;
  outline: none;
  transition: color 500ms var(--sfl-ease), border-color 500ms var(--sfl-ease);
}
.sfl-fill {
  position: absolute;
  inset: 0;
  z-index: -1;
  background: var(--sfl-ink, #17191a);
  transform: scaleY(0);
  transform-origin: 50% 100%; /* idle: collapses toward the bottom edge */
  transition: transform 500ms var(--sfl-ease); /* transform only: the origin must switch instantly */
  pointer-events: none;
}
.sfl-label,
.sfl-icon {
  display: block;
  transition: transform 700ms var(--sfl-ease);
}
.sfl-label {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.sfl-icon {
  flex: none;
}

/* the active state: a real pointer's hover, or keyboard focus. Taps on a touch screen leave nothing behind. */
@media (hover: hover) {
  .sfl-row:hover {
    color: var(--sfl-paper, #f2f2f2);
  }
  .sfl-row:hover .sfl-fill {
    transform: scaleY(1);
    transform-origin: 50% 0%; /* hover: grows from the top edge */
  }
  .sfl-row:hover .sfl-label {
    transform: translateX(15px);
  }
  .sfl-row:hover .sfl-icon {
    transform: translateX(-15px);
  }
}
.sfl-row:focus-visible {
  color: var(--sfl-paper, #f2f2f2);
}
.sfl-row:focus-visible .sfl-fill {
  transform: scaleY(1);
  transform-origin: 50% 0%;
}
.sfl-row:focus-visible .sfl-label {
  transform: translateX(15px);
}
.sfl-row:focus-visible .sfl-icon {
  transform: translateX(-15px);
}

@media (prefers-reduced-motion: reduce) {
  .sfl-row,
  .sfl-fill,
  .sfl-label,
  .sfl-icon {
    transition-duration: 0.01ms;
  }
}
/* high-contrast modes override backgrounds, so the fill can't carry focus there */
@media (forced-colors: active) {
  .sfl-row:focus-visible {
    outline: 2px solid CanvasText;
    outline-offset: 2px;
  }
}
```

### 3. Use it
Set the two colours on the list, or on any ancestor, to match the page. The fallbacks (`#17191a` ink on `#f2f2f2` paper) only apply where nothing sets them:
```tsx
import SlidingFillList from "@/components/ui/SlidingFillList";

const projects = [
  { label: "Typography Principles (2019)", href: "/work/typography" },
  { label: "Colors Combinations (2020)", href: "/work/colors" },
  { label: "Instagram", href: "https://instagram.com/yourname", external: true },
];

<section style={{ background: "#f2f2f2", color: "#17191a", padding: "80px" }}>
  <SlidingFillList items={projects} />
</section>

// a dark section: swap the two, in any stylesheet, in any order
<SlidingFillList items={projects} className="on-dark" />
/* .on-dark { --sfl-ink: #f2f2f2; --sfl-paper: #17191a; } */
```

## Why these values
- **The origin switch is the whole effect.** `transform-origin` isn't in the transition list, so it flips the moment hover starts or ends while `scaleY` eases. Leaving a row sets its origin to the bottom, so its fill collapses downward. Entering the next row sets its origin to the top, so its fill grows downward. Both move down at once, so the eye sees one bar travelling.
- **The fill at 500ms, the text at 700ms, both `cubic-bezier(0.4, 0, 0.2, 1)`:** the fill arrives first, and the label keeps gliding after it, so it reads as riding on the bar rather than fixed to it. Keep the two durations different.
- **15px apart, opposite ways:** the label moves right and the arrow moves left. Pushing apart reads as "open", and 15px stays inside the row.
- **`isolation: isolate`:** the fill sits at `z-index: -1` behind the text. Without a stacking context on the row, it sinks behind the nearest ancestor background and the hover shows nothing.
- **`border-bottom: currentColor`:** the rule turns the page colour with the text on hover, so the filled row has no seam.

## Failure patterns to avoid
Each was measured in a fresh Next.js 16 project:
- **Colour tokens in `tailwind.config.js`** (`bg-themeColor`) on Tailwind v4: the classes don't exist, and hovering showed no fill at all.
- **A `z-index: -1` fill without `isolation: isolate` on the row:** on a section with its own background, the fill painted behind it and stayed invisible.
- **`:hover` without `@media (hover: hover)`:** a tap on a phone left the row stuck filled.
- **No `:focus-visible` state:** keyboard users got no indication of which row they were on.
- **`transition: all`** or a transitioned `transform-origin`: the origin animates instead of switching. Measured 170ms into a hand-off on a 73px row: with the transform alone, the leaving fill covered 39–72px and the entering one 0–39px, one bar crossing the rule. With `transition: all`, each row held its own bar floating mid-row (21–54px and 15–54px).
- **Defining the colour variables on the component's own class.** A user's override class of equal specificity then loses or wins on stylesheet order alone. In testing, a dark-section override came out dark-on-dark. Read the variables with `var(--sfl-ink, fallback)` and let the page define them.

## Verify before you finish
Run each check, fix anything that fails, and say which ones you ran:
1. `npx tsc --noEmit` and `npm run build` both succeed.
2. Hover a row on the page's real background: it fills solid, and the text turns the background colour.
3. Move the pointer slowly down three rows: the fill reads as one bar sliding down. Halfway between two rows, the upper fill is shrinking to its bottom while the lower one grows from its top.
4. Tab through the list: each focused row fills.
5. In device emulation (touch), tap a row whose link stays on the page: nothing stays filled.
6. With `prefers-reduced-motion: reduce` emulated, the states switch without movement.
7. A long label truncates with an ellipsis instead of pushing the arrow out.
