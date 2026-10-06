---
description: Note minimap. A vertical rail of section cards (thumbnail plus title) at the page edge that follows your reading on a soft, underdamped spring, with a viewfinder that locks onto the current section; click a card to glide there. For Next.js (App or Pages Router), no dependencies.
argument-hint: "[optional: where to use it, e.g. 'the case-study pages in app/work/[slug]/page.tsx']"
model: claude-opus-5-5
effort: max
---

# Note minimap

Build the note minimap in the current project and use it where `$ARGUMENTS` says. If `$ARGUMENTS` is empty, create the component and show it on a long page with five sections.

## What it looks like
A narrow rail sits fixed at the left edge, vertically centred, its ends fading out. It holds one small card (72×40px) per section: the section's thumbnail with its title on an ink band along the bottom, or just the title on ink when there's no thumbnail. The rail's centre is the reading line, 40% down the screen. As you scroll, the strip of cards glides so the position you're reading sits at that centre. It moves on a soft, underdamped spring, so it floats and settles with a little overshoot. Four corner marks (the viewfinder) frame the card for the section you're in, on their own slightly quicker spring. Cards near the reading position are brighter. Click a card, or focus it and press Enter, and the page glides to that section. It shows at most five cards, hides under 900px wide, and goes to sleep when nothing moves.

## Before you write code
1. **The components folder.** Read `tsconfig.json` (or `jsconfig.json`) `compilerOptions.paths` and put both files wherever `@/components/...` resolves: `components/ui/` at the root, or `src/components/ui/`. In a JavaScript project, save the component as `NoteMinimap.jsx` and drop the types.
2. **The router.** In the App Router, the component imports its own CSS. In the Pages Router, import `NoteMinimap.css` in `pages/_app.tsx` instead and delete the import line from the component, since Pages only allows global CSS there.
3. **The sections.** Find the page's significant sections, at most five: the chapters, not every paragraph. Each one opts in with `data-minimap` on its wrapper, `data-label` for the card's title (it falls back to the section's first heading), and `data-thumb` for an image URL if there is one. Give the component the selector of the element that holds them (`scope`, default `main`).
4. **Colours.** The rail reads `--nm-ink` and `--nm-paper` (defaults `#17191a` and `#f2f2f2`). Set them on `.nm` or `:root` to the project's ink and background.
5. **Room at the left.** The rail is fixed 24px from the left edge and 96px wide. Make sure the page's content column doesn't run under it at 900px and up, or move the rail with `.nm { left: … }`.

## Build

### 1. The component: `components/ui/NoteMinimap.tsx`
It's a Client Component; you can render it from a Server Component page.
```tsx
"use client";

import { useEffect, useRef, useState } from "react";
import "./NoteMinimap.css";

type Mark = { el: HTMLElement; y: number; label: string; thumb?: string };

const W = 72, H = 40, GAP = 16; // one card size for every section
const LEFT = 14; // every card's left edge inside the rail
const PAD = 5; // the viewfinder's clearance round a card
const READ = 0.4; // the reading line, as a share of the viewport height
const OMEGA = 2 * Math.PI * 0.8, ZETA = 0.55; // the strip: low frequency, a little overshoot
const F_OMEGA = 2 * Math.PI * 1.3, F_ZETA = 0.7; // the viewfinder: a touch quicker, so it hugs the card
const SHOWN = "(min-width: 900px)"; // keep in step with the media query in NoteMinimap.css

type Props = {
  /** CSS selector of the element that holds the sections */
  scope?: string;
  /** at most this many cards (the first sections in the page) */
  max?: number;
  label?: string;
};

export default function NoteMinimap({ scope = "main", max = 5, label = "Page minimap" }: Props) {
  const railRef = useRef<HTMLElement>(null);
  const stripRef = useRef<HTMLDivElement>(null);
  const finderRef = useRef<HTMLSpanElement>(null);
  const cardRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const [marks, setMarks] = useState<Mark[]>([]);

  // Read the sections once the page is laid out. A section joins with data-minimap, and names itself with
  // data-label (falling back to its first heading) and, optionally, data-thumb (an image URL).
  useEffect(() => {
    const els = [...document.querySelectorAll<HTMLElement>(`${scope} [data-minimap]`)].slice(0, max);
    const list = els.map((el, i) => {
      const heading = el.querySelector<HTMLElement>("h1, h2, h3");
      return {
        el: heading ?? el, // scroll to the heading, not to a wrapper whose top sits a margin above it
        y: i * (H + GAP) + H / 2,
        label: el.dataset.label || heading?.textContent?.trim() || `Section ${i + 1}`,
        thumb: el.dataset.thumb || undefined,
      };
    });
    const raf = requestAnimationFrame(() => setMarks(list));
    return () => cancelAnimationFrame(raf);
  }, [scope, max]);

  useEffect(() => {
    if (!marks.length) return;
    const rail = railRef.current!, strip = stripRef.current!, finder = finderRef.current!;
    const shown = window.matchMedia(SHOWN);
    const still = window.matchMedia("(prefers-reduced-motion: reduce)");
    let tops: number[] = [];
    let railH = rail.clientHeight;
    let x = 0, v = 0, last = 0, raf = 0, first = true, running = false, lastActive = -1;
    const F = { y: 0, vy: 0 }; // the viewfinder's centre and velocity

    // Which section the reading line is in, and the rail position between that card and the next.
    const read = () => {
      const line = window.scrollY + READ * window.innerHeight;
      let i = 0;
      while (i < marks.length - 1 && tops[i + 1] <= line) i++;
      if (i === marks.length - 1) return { i, y: marks[i].y };
      const k = Math.min(1, Math.max(0, (line - tops[i]) / Math.max(1, tops[i + 1] - tops[i])));
      return { i, y: marks[i].y + (marks[i + 1].y - marks[i].y) * k };
    };
    // A damped spring, integrated in four sub-steps per frame so a long frame can't blow it up.
    const spring = (pos: number, vel: number, goal: number, w: number, z: number, dt: number) => {
      for (let s = 0; s < 4; s++) {
        const h = dt / 4;
        vel += (w * w * (goal - pos) - 2 * z * w * vel) * h;
        pos += vel * h;
      }
      return [pos, vel];
    };
    const loop = (now: number) => {
      const dt = last ? Math.min((now - last) / 1000, 0.05) : 1 / 60;
      last = now;
      const r = read();
      const off = railH / 2; // the strip puts rail position x at the rail's centre
      if (first || still.matches) {
        x = r.y;
        v = 0;
      } else {
        [x, v] = spring(x, v, r.y, OMEGA, ZETA, dt);
      }
      const shift = off - x;
      const goal = marks[r.i].y + shift;
      if (first || still.matches) {
        F.y = goal;
        F.vy = 0;
      } else {
        [F.y, F.vy] = spring(F.y, F.vy, goal, F_OMEGA, F_ZETA, dt);
      }
      first = false;
      strip.style.transform = `translate3d(0, ${shift.toFixed(2)}px, 0)`;
      finder.style.transform = `translate3d(${LEFT - PAD}px, ${(F.y - H / 2 - PAD).toFixed(2)}px, 0)`;
      if (r.i !== lastActive || Math.abs(v) > 0.01) {
        marks.forEach((m, i) => {
          const el = cardRefs.current[i];
          if (!el) return;
          el.style.setProperty("--t", i === r.i ? "1" : Math.max(0, 1 - Math.abs(m.y - x) / 60).toFixed(3));
          if (i === r.i) el.setAttribute("aria-current", "location");
          else el.removeAttribute("aria-current");
        });
        lastActive = r.i;
      }
      // Sleep once everything has settled; a scroll, a resize or a layout change wakes it.
      const settled = Math.abs(r.y - x) < 0.05 && Math.abs(v) < 0.05 && Math.abs(F.vy) < 0.05 && Math.abs(F.y - goal) < 0.05;
      if (settled) {
        running = false;
        return;
      }
      raf = requestAnimationFrame(loop);
    };
    const wake = () => {
      if (running || !shown.matches) return;
      running = true;
      last = 0;
      raf = requestAnimationFrame(loop);
    };
    // Section tops are measured on mount and whenever the layout changes, never per frame.
    const measure = () => {
      tops = marks.map((m) => m.el.getBoundingClientRect().top + window.scrollY);
      railH = rail.clientHeight;
      wake();
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(document.querySelector(scope) ?? document.body);
    window.addEventListener("scroll", wake, { passive: true });
    window.addEventListener("resize", measure);
    shown.addEventListener("change", measure);
    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      window.removeEventListener("scroll", wake);
      window.removeEventListener("resize", measure);
      shown.removeEventListener("change", measure);
    };
  }, [marks, scope]);

  const go = (el: HTMLElement) => {
    const top = el.getBoundingClientRect().top + window.scrollY - READ * window.innerHeight + 8;
    const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.scrollTo({ top, behavior: still ? "auto" : "smooth" });
  };

  return (
    <nav ref={railRef} className="nm" aria-label={label}>
      <div ref={stripRef} className="nm__strip">
        {marks.map((m, i) => (
          // the button is the card's whole row, an easy target; the visible card sits inside it
          <button
            key={i}
            ref={(el) => {
              cardRefs.current[i] = el;
            }}
            type="button"
            className="nm__hit"
            style={{ top: m.y - (H + GAP) / 2, height: H + GAP }}
            onClick={() => go(m.el)}
            aria-label={`Go to ${m.label}`}
            title={m.label}
          >
            <span className="nm__card" style={{ left: LEFT, width: W, height: H, marginTop: -H / 2 }}>
              {m.thumb && (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={m.thumb} alt="" draggable={false} />
              )}
              <span className="nm__title">{m.label}</span>
            </span>
          </button>
        ))}
      </div>
      <span ref={finderRef} className="nm__finder" aria-hidden="true" style={{ width: W + 2 * PAD, height: H + 2 * PAD }}>
        <i />
        <i />
        <i />
        <i />
      </span>
    </nav>
  );
}
```

### 2. The CSS: `components/ui/NoteMinimap.css`
```css
/* Note minimap: a vertical strip of section cards whose centre is the reading line (40% down).
   The strip glides through the viewfinder on a soft spring. Colours come from two variables. */
.nm {
  --nm-ink: #17191a;
  --nm-paper: #f2f2f2;
  position: fixed;
  left: 24px;
  top: 8vh;
  height: 64vh;
  width: 96px;
  overflow: hidden;
  z-index: 3;
  display: none;
  -webkit-mask-image: linear-gradient(transparent, #000 16%, #000 84%, transparent);
  mask-image: linear-gradient(transparent, #000 16%, #000 84%, transparent);
}
/* keep in step with SHOWN in NoteMinimap.tsx */
@media (min-width: 900px) {
  .nm {
    display: block;
  }
}
.nm__strip {
  position: absolute;
  left: 0;
  top: 0;
  width: 100%;
  will-change: transform;
}
/* each card is a full-width row you can click; the visible card sits inside it */
.nm__hit {
  position: absolute;
  left: 0;
  width: 100%;
  padding: 0;
  margin: 0;
  display: block;
  border: 0;
  background: none;
  cursor: pointer;
  --t: 0;
}
.nm__card {
  position: absolute;
  top: 50%;
  display: block;
  overflow: hidden;
  pointer-events: none;
  background: var(--nm-ink);
  opacity: calc(0.5 + 0.5 * var(--t));
}
.nm__card img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
/* the section's title on an ink band along the bottom (the whole card is ink when there's no thumbnail) */
.nm__title {
  position: absolute;
  inset: auto 0 0 0;
  padding: 3px 5px;
  background: var(--nm-ink);
  color: var(--nm-paper);
  font: 600 7.5px/1.15 system-ui, sans-serif;
  letter-spacing: 0;
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.nm__hit:hover {
  --t: 1;
}
.nm__hit:focus-visible {
  outline: 1px solid var(--nm-ink);
  outline-offset: -1px;
}
/* the viewfinder: four corner marks that lock onto the card you're reading */
.nm__finder {
  position: absolute;
  left: 0;
  top: 0;
  pointer-events: none;
  --arm: 7px;
}
.nm__finder i {
  position: absolute;
  width: var(--arm);
  height: var(--arm);
  border: 0 solid var(--nm-ink);
}
.nm__finder i:nth-child(1) { left: 0; top: 0; border-left-width: 1px; border-top-width: 1px; }
.nm__finder i:nth-child(2) { right: 0; top: 0; border-right-width: 1px; border-top-width: 1px; }
.nm__finder i:nth-child(3) { left: 0; bottom: 0; border-left-width: 1px; border-bottom-width: 1px; }
.nm__finder i:nth-child(4) { right: 0; bottom: 0; border-right-width: 1px; border-bottom-width: 1px; }
```

### 3. Use it
```tsx
import NoteMinimap from "@/components/ui/NoteMinimap";

export default function Page() {
  return (
    <main id="note">
      <NoteMinimap scope="#note" />
      <section data-minimap data-label="The brief" data-thumb="/work/brief.jpg">
        <h2>The brief</h2>
        …
      </section>
      <section data-minimap data-label="Process">
        <h2>Process</h2>
        …
      </section>
    </main>
  );
}
```

## Why these values
- **A strip spring at 0.8Hz with damping 0.55:** low frequency and underdamped, so the strip floats after the page and settles with a small overshoot (about 13px when you jump a whole section). A critically damped spring reads mechanical; less damping wobbles.
- **A viewfinder spring at 1.3Hz with damping 0.7:** a touch quicker and steadier than the strip, so the corner marks hug the card while the strip is still drifting. Two springs at different rates are what give it depth.
- **The reading line at 40%:** that's where the eye actually is on a long page, a little above the middle. Between two sections the strip interpolates, so it glides continuously instead of jumping card to card.
- **At most five cards:** a minimap of every paragraph is noise. Five chapters is a map.
- **Sleeping when settled:** the loop stops once the strip and viewfinder are at rest, and wakes on scroll, resize or a layout change. A still page costs nothing.
- **Measuring section tops only on layout change:** reading `getBoundingClientRect` for every section on every frame would force layout 60 times a second.

## Failure patterns to avoid
Measured on Next.js 16.3.8 in Chromium, Firefox and WebKit, 2026-10-05, by breaking the component on purpose:
- **A loop that never sleeps.** With nothing moving, it still requested 61 animation frames a second in Chromium, 65 in WebKit and 167 in Firefox. Keep the settle check that returns without asking for another frame.
- **Ignoring reduced motion.** The strip went on springing through about 160 to 170px of travel after a jump. Under `prefers-reduced-motion: reduce` the strip and viewfinder must land at once, and card clicks must scroll instantly.
- **Scrolling to the section wrapper instead of its heading.** The wrapper's top sits a margin above the heading, so a click lands short. The component targets the first `h1`, `h2` or `h3` inside the section.
- **Snapping the strip card to card.** It reads as a stepper, not a map of your reading. Interpolate between sections as written.

## Verify before you finish
Run each check, fix anything that fails, and say which ones you ran:
1. `npx tsc --noEmit` and `npm run build` both succeed.
2. At 1280px wide, the rail shows one card per marked section, at most five, each named "Go to …" for screen readers. A section without `data-thumb` shows a title-only card.
3. Scroll into the third section and stop: the viewfinder frames the third card, and the strip drifts a little past, then settles.
4. Click the fifth card: the page glides there and the section's heading lands near the reading line. Focus the second card and press Enter: same.
5. Once everything is still, the rail requests no animation frames (check the Performance panel, or count `requestAnimationFrame` calls for a second).
6. Under 900px wide, the rail is hidden.
7. With `prefers-reduced-motion: reduce` emulated, the strip and viewfinder land at once with no spring.
