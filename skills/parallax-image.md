---
description: Parallax image. A photograph moves inside a still frame as the frame crosses the screen, in one of three measured variants. Drift (it moves slower than its frame), zoom (1.45x scrubbing to 1x, Telha Clarke) or settle (a slow 1.12x to 1x on entry, OH Architecture). Wraps any img, next/image or video; the picture always covers its frame. For Next.js (App or Pages Router) + GSAP ScrollTrigger.
argument-hint: "[optional: where and which variant, e.g. 'the project hero images, drift' or 'the about photo, settle']"
model: claude-opus-5-5
effort: max
---

# Parallax image

Build the parallax image in the current project and use it where `$ARGUMENTS` says. If `$ARGUMENTS` is empty, create the component and show one image in each mode, with enough space around them to scroll.

## What it looks like
The frame (a fixed aspect-ratio box) scrolls with the page like any other block. The picture inside it moves on its own.
- **`drift`:** as the frame travels up the screen, the picture travels down inside it, by 8% of the frame's height each way. The picture seems to sit further back than the page. It's tied to the scroll position, so it moves only while you scroll.
- **`zoom`:** the picture enters at 1.45× and scrubs down to 1× as the frame rises from the bottom of the screen to its middle (measured on telhaclarke.com.au, 2026-10-05). It holds at 1× after that.
- **`settle`:** the picture waits at 1.12× and, when the frame comes into view, eases to 1× once over 1.8s (measured on oharchitecture.com.au). It doesn't replay.

In every mode the picture covers the frame at every moment; no edge or background ever shows. With reduced motion the picture simply sits still at 1×.

## Before you write code
1. **GSAP.** Check `package.json` for `gsap` (3.12 or later) and `@gsap/react`. If either is missing, run `npm install gsap @gsap/react`. ScrollTrigger ships inside `gsap`.
2. **The components folder.** Read `tsconfig.json` (or `jsconfig.json`) `compilerOptions.paths` and put the file wherever `@/components/...` resolves: `components/ui/` at the root, or `src/components/ui/`. In a JavaScript project, save it as `ParallaxImage.jsx` and drop the types.
3. **The media.** Pass the image as the child: `<img>`, `next/image` with `fill` (not `width`/`height`), or `<video>`. The component stretches it to cover the frame with `object-fit: cover`, so don't give the child its own size.
4. **The frame size.** The frame takes the width of its container. Set its shape with `ratio` (default `"3 / 2"`), and its width through the container or `style`.
5. **Smooth scrolling.** If the project uses Lenis, it must already drive ScrollTrigger (`lenis.on("scroll", ScrollTrigger.update)`); the component needs nothing more.

## Build

### 1. The component: `components/ui/ParallaxImage.tsx`
```tsx
"use client";

import { useRef, type CSSProperties, type ReactNode } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useGSAP } from "@gsap/react";

gsap.registerPlugin(ScrollTrigger, useGSAP);

type Mode = "drift" | "zoom" | "settle";

type Props = {
  /** the image (or video): <img>, next/image with `fill`, <video>. It is stretched to cover the frame. */
  children: ReactNode;
  /**
   * drift:  the picture moves slower than its frame as the frame crosses the screen
   * zoom:   the picture starts at 1.45x and scrubs down to 1x by the time the frame reaches mid-screen
   * settle: the picture eases from 1.12x to 1x once, as the frame comes into view
   */
  mode?: Mode;
  /** the frame's aspect ratio, e.g. "16 / 10" */
  ratio?: string;
  /** drift only: how far the picture travels, as a share of the frame height (each way) */
  travel?: number;
  className?: string;
  style?: CSSProperties;
};

export default function ParallaxImage({ children, mode = "drift", ratio = "3 / 2", travel = 0.08, className, style }: Props) {
  const frame = useRef<HTMLDivElement>(null);
  const layer = useRef<HTMLDivElement>(null);
  const bleed = travel + 0.02; // the extra picture above and below the frame, so an edge never shows

  useGSAP(
    () => {
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
      const f = frame.current!;
      const l = layer.current!;
      if (mode === "drift") {
        // The layer is (1 + 2 * bleed) of the frame's height; travel is measured against the frame.
        const pct = (travel / (1 + 2 * bleed)) * 100;
        gsap.fromTo(l, { yPercent: -pct }, { yPercent: pct, ease: "none", scrollTrigger: { trigger: f, start: "top bottom", end: "bottom top", scrub: true } });
      } else if (mode === "zoom") {
        gsap.fromTo(l, { scale: 1.45 }, { scale: 1, ease: "none", scrollTrigger: { trigger: f, start: "top bottom", end: "center 55%", scrub: 0.6 } });
      } else {
        gsap.fromTo(l, { scale: 1.12 }, { scale: 1, duration: 1.8, ease: "power2.out", scrollTrigger: { trigger: f, start: "top 88%", once: true } });
      }
    },
    { scope: frame, dependencies: [mode, travel], revertOnUpdate: true },
  );

  const tall = mode === "drift";
  return (
    <div ref={frame} className={className} style={{ position: "relative", overflow: "hidden", aspectRatio: ratio, ...style }}>
      <div
        ref={layer}
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: tall ? `${-bleed * 100}%` : 0,
          bottom: tall ? `${-bleed * 100}%` : 0,
          willChange: "transform",
        }}
      >
        <div className="parallax-image__media" style={{ position: "absolute", inset: 0 }}>
          {children}
        </div>
      </div>
      {/* stretch any child (img, video, next/image) to cover the layer */}
      <style>{".parallax-image__media > img, .parallax-image__media > video { width: 100%; height: 100%; object-fit: cover; display: block; }"}</style>
    </div>
  );
}
```

### 2. Use it
```tsx
import Image from "next/image";
import ParallaxImage from "@/components/ui/ParallaxImage";

<ParallaxImage mode="drift" ratio="16 / 10">
  <Image src="/work/harlan.jpg" alt="Harlan House at dusk" fill sizes="(min-width: 1024px) 60vw, 100vw" />
</ParallaxImage>

<ParallaxImage mode="zoom" ratio="4 / 3">
  <img src="/work/coldwater.jpg" alt="Coldwater from the creek" />
</ParallaxImage>

<ParallaxImage mode="settle">
  <video src="/films/studio.mp4" muted loop playsInline autoPlay />
</ParallaxImage>
```

## Why these values
- **Drift of 8% each way, with a 10% bleed above and below:** the picture is 1.2× the frame's height, so its travel never reaches an edge. More travel needs more bleed (the component adds 2% over `travel` automatically), and more bleed crops more of the picture.
- **`scrub: true` on drift:** the picture is fixed to the scroll position, so it never lags or floats after you stop. It reads as depth, not as an animation.
- **Zoom ends at mid-screen (`center 55%`):** by the time the picture is where you'd look at it, it's at its true framing. The 0.6s scrub smoothing keeps fast wheel flicks from stepping.
- **Settle uses `power2.out` over 1.8s, once:** an image settling, not a text landing. It's softer than the `power4.out` used for type, and slow enough to read as the camera, not the page. Playing it once keeps a returning visitor from seeing it again.

## Failure patterns to avoid
Measured on Next.js 16.3.8 with GSAP 3.15, in Chromium, Firefox and WebKit, 2026-10-05:
- **Drift with no bleed** (the picture the same size as its frame). The suite's "the picture always covers the frame" check failed in Chromium, Firefox and WebKit: the frame's background showed along the top or bottom edge as soon as the picture moved.
- **Sizing the child yourself.** A `next/image` with `width`/`height`, or an `<img>` with a fixed height, doesn't cover the moving layer. Use `fill`, or a plain `<img>` with no size. (A guard, not measured; the suite confirms `next/image` with `fill` covers.)
- **Animating the frame instead of an inner layer.** The page around it would move with it. Only the inner layer transforms. (A guard, not measured.)
- **Rebuilding the triggers without reverting the old ones when props change.** GSAP would stack the animations. The component reverts them on update. (A guard, not measured.)

## Verify before you finish
Run each check, fix anything that fails, and say which ones you ran:
1. `npx tsc --noEmit` and `npm run build` both succeed.
2. Drift: scroll slowly past the frame. The picture moves down inside it as the frame moves up, steadily, and no edge or background ever shows.
3. Zoom: the picture is clearly enlarged as the frame enters, and it's at its normal size by the time the frame's centre reaches the middle of the screen.
4. Settle: the picture eases out of a slight zoom once when the frame appears. Scroll away and back: it doesn't replay.
5. With `prefers-reduced-motion: reduce` emulated, nothing moves and nothing is enlarged.
