---
description: Number roll. Digits roll to a new value like a counter, right-most digit first, while colons, commas and letters stay put. For a clock, a count, a price, a date, a project number. The value is real text in the page; the rolling strips are CSS-generated, so copy, search and screen readers get the number once. CSS transitions, no animation library. For Next.js (App or Pages Router).
argument-hint: "[optional: which number, e.g. 'the local time in the footer' or 'the project count on the studio page']"
model: claude-opus-5-5
effort: max
---

# Number roll

Build the number roll in the current project and use it where `$ARGUMENTS` says. If `$ARGUMENTS` is empty, create the component and show it on a local-time clock that updates every minute and on a count further down the page.

## What it looks like
When the value changes, each digit rolls along a 0 to 9 strip to its new digit in 1.1s on `cubic-bezier(0.16, 1, 0.3, 1)`. The right-most digit moves first and each place to its left follows 60ms later, like a counter turning over. Anything that isn't a digit (the colon in 4:38, the comma in 1,284, "PM") stays put. Each digit runs along its strip, so 8 to 4 rolls back through 7, 6 and 5; it doesn't wrap round like a mechanical counter. The digits are tabular, so the width holds as they change; the symbols keep their own width. A number that's already on screen when the page loads just shows its value. One that's off screen waits at zero and rolls up once most of it is in view. Under reduced motion the digits change without rolling.

## Before you write code
1. **No dependencies.** It's a small Client Component and CSS transitions.
2. **The components folder.** Read `tsconfig.json` (or `jsconfig.json`) `compilerOptions.paths` and put both files wherever `@/components/...` resolves: `components/ui/` at the root, or `src/components/ui/`. In a JavaScript project, save it as `NumberRoll.jsx` and drop the types.
3. **The router.** In the App Router, the component imports its own CSS. In the Pages Router, import `NumberRoll.css` in `pages/_app.tsx` instead and delete the import line from the component.
4. **The value.** Pass the formatted string you want shown (`"4:38 PM"`, `"1,284"`, `"£2.4m"`), or a number. Format it yourself (`toLocaleString`, `Intl.DateTimeFormat`); the component only rolls digits.
5. **The type.** It inherits the font and size. The font needs tabular figures (most grotesques have them) for the width to hold; with proportional figures it still works, but the width shifts as digits change. Only the digit columns are set tabular. Don't move `tabular-nums` onto the whole number, or onto a parent: some faces widen their punctuation in the tabular set (see the failure patterns).
6. **A clock.** A time that changes while the page is open must be rendered on the client, or the server's time and the browser's will disagree at hydration. Start the state empty, set it in an effect, and render the `NumberRoll` once it has a value.

## Build

### 1. The component: `components/ui/NumberRoll.tsx`
```tsx
"use client";

import { useEffect, useRef, type CSSProperties } from "react";
import "./NumberRoll.css";

/**
 * Digits roll to a new value, right to left, like an odometer. Anything that isn't a digit (":", ",", "PM")
 * stays put. A number that's off screen when the page loads waits at zero and rolls in when it's seen; one
 * that's already on screen just shows its value. Every later change rolls.
 */
export default function NumberRoll({ value, className, style }: { value: string | number; className?: string; style?: CSSProperties }) {
  const text = String(value);
  const root = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const el = root.current!;
    const r = el.getBoundingClientRect();
    const onScreen = r.top < window.innerHeight && r.bottom > 0;
    if (onScreen || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      // on screen at load: it just shows its value; from now on, changes roll
      el.setAttribute("data-armed", "");
      return;
    }
    // off screen: drop to zero while unseen, then roll up once it's in view
    el.setAttribute("data-zero", "");
    void el.offsetWidth; // commit the zeros before transitions turn on
    el.setAttribute("data-armed", "");
    const io = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          el.removeAttribute("data-zero");
          io.disconnect();
        }
      },
      { threshold: 0.6 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  const chars = text.split("");
  // each digit's place counted from the right: the right-most digit rolls first
  const place: number[] = [];
  for (let i = chars.length - 1, n = 0; i >= 0; i--) place[i] = /\d/.test(chars[i]) ? n++ : -1;
  return (
    <span ref={root} className={["number-roll", className].filter(Boolean).join(" ")} style={style}>
      {/* the value, once, for screen readers and copy: the columns below are decoration */}
      <span className="number-roll__text">{text}</span>
      <span className="number-roll__view" aria-hidden="true">
        {chars.map((c, i) => {
          const fromRight = chars.length - 1 - i; // keys from the right, so the columns survive a length change
          if (!/\d/.test(c)) return <span key={`s${fromRight}`} className="number-roll__sym" data-c={c} />;
          return (
            <span key={`d${fromRight}`} className="number-roll__col" style={{ "--d": Number(c), "--i": place[i] } as CSSProperties}>
              <span className="number-roll__ghost">{c}</span>
            </span>
          );
        })}
      </span>
    </span>
  );
}
```

### 2. The CSS: `components/ui/NumberRoll.css`
```css
/* Number roll: each digit is a column holding the strip 0-9 (generated content, so it's never in the page's
   text). One custom property, --d, picks the digit; a transition rolls the strip. */
.number-roll {
  position: relative;
  display: inline-block;
  white-space: nowrap;
}
/* the real value: visually hidden, but read by screen readers and part of innerText */
.number-roll__text {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
}
.number-roll__col {
  position: relative;
  display: inline-block;
  font-variant-numeric: tabular-nums; /* the digits only: some faces' tabular set also widens ":" "," "." to a full figure */
  height: 1em;
  line-height: 1em;
  clip-path: inset(0); /* a window one digit tall; clip-path, not overflow, so the baseline stays on the digit */
}
.number-roll__ghost {
  visibility: hidden; /* sizes the column to one digit */
}
.number-roll__col::before {
  content: "0\A 1\A 2\A 3\A 4\A 5\A 6\A 7\A 8\A 9";
  white-space: pre;
  position: absolute;
  left: 0;
  top: 0;
  width: 100%;
  text-align: center;
  line-height: 1em;
  transform: translateY(calc(var(--d) * -1em));
  /* right to left, 60ms apart: the right-most digit moves first, like an odometer */
  transition: transform 1.1s cubic-bezier(0.16, 1, 0.3, 1) calc(var(--i) * 60ms);
}
.number-roll:not([data-armed]) .number-roll__col::before {
  transition: none;
}
.number-roll[data-zero] .number-roll__col {
  --d: 0 !important;
}
.number-roll__sym::before {
  content: attr(data-c);
  white-space: pre;
}
@media (prefers-reduced-motion: reduce) {
  .number-roll__col::before {
    transition: none;
  }
}
```

### 3. Use it
```tsx
import NumberRoll from "@/components/ui/NumberRoll";

<p className="text-8xl">
  <NumberRoll value={projects.length} />
</p>
```
A local-time clock (a Client Component):
```tsx
"use client";

import { useEffect, useState } from "react";
import NumberRoll from "@/components/ui/NumberRoll";

const fmt = new Intl.DateTimeFormat("en-US", { hour: "numeric", minute: "2-digit", timeZone: "America/Chicago" });

export default function LocalTime() {
  const [now, setNow] = useState<string | null>(null);
  useEffect(() => {
    const tick = () => setNow(fmt.format(new Date()));
    tick();
    const id = setInterval(tick, 15_000);
    return () => clearInterval(id);
  }, []);
  return now ? <NumberRoll value={now} /> : null;
}
```

## Why these values
- **1.1s on `cubic-bezier(0.16, 1, 0.3, 1)`:** the strip leaves fast and settles slowly, so the new digit is legible early and the motion finishes quietly.
- **Right to left, 60ms apart:** the ones place moves first, the way a counter turns over, so a change reads as counting rather than as a block swap.
- **The strip is generated content (`::before`), and the value sits once in a visually hidden span:** the page's text, copy-paste and screen readers get "4:38 PM", never "0123456789".
- **The column clips with `clip-path`, not `overflow: hidden`:** an inline-block with `overflow: hidden` takes its bottom edge as its baseline, which lifts every digit above the text around it.
- **Off screen at load, wait at zero:** a count that has already finished by the time you scroll to it is wasted. On screen at load, show the value: rolling the first thing a visitor sees delays it.

## Failure patterns to avoid
Measured on Next.js 16.3.8 and React 19.2.8 in Chromium 153, Firefox 155 and WebKit 26.6 (Playwright 1.63), 2026-10-05:
- **`tabular-nums` on the whole value.** Measured in Helvetica Now Display (Chromium 153): its tabular set gives the colon, comma and period a full figure's width (104.7px against 32.5px at 170px), so 4:38 read as "4 : 38". Arial and Georgia don't change. The component sets tabular figures on the digit columns only.
- **`overflow: hidden` for the digit window.** The digits sat 14.5 to 15px off the baseline of the text beside them at 96px, in Chromium, Firefox and WebKit. `clip-path: inset(0)` clips the same window and keeps the baseline.
- **Turning transitions on in the same style change that drops an off-screen number to zero.** Without the forced reflow (`void el.offsetWidth`), the number rolled down to zero instead of waiting there; it was still moving when checked, in all three engines.
- **The digits 0 to 9 as real text.** The page's text, copy-paste and screen readers would read "0123456789" for every digit. The strips are generated content for that reason. (A guard, not measured.)
- **A clock rendered on the server.** The server's minute and the browser's minute can differ, which is a hydration mismatch. Set the time in an effect, as in the example above. (A guard, not measured.)

## Verify before you finish
Run each check, fix anything that fails, and say which ones you ran:
1. `npx tsc --noEmit` and `npm run build` both succeed.
2. View the page source (or `curl` it): the value is in the HTML as text. In the browser, the element's `innerText` is the value, once.
3. Change the value: the digits roll, right-most first, and land exactly on the new digits; the symbols don't move and the width holds.
4. The digits sit on the same baseline as the text around them.
5. A number below the fold waits at zero and rolls up as you scroll to it; one at the top shows its value at load without rolling.
6. With `prefers-reduced-motion: reduce` emulated, the digits change without rolling.
