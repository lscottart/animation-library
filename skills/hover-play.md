---
description: Hover play. A video card holds its poster until you point at it, then plays; leave and it pauses on the frame it reached, with a hairline along the bottom showing where the loop is. Keyboard focus plays it too, and on touch screens it plays while it's mostly in view. Costs nothing while paused. No library. For Next.js (App or Pages Router).
argument-hint: "[optional: where, e.g. 'the project grid: each card's walkthrough clip']"
model: claude-opus-5-5
effort: max
---

# Hover play

Build the hover-play video card in the current project and use it where `$ARGUMENTS` says. If `$ARGUMENTS` is empty, create the component and show two cards side by side, one with the timecode.

## What it looks like
The card shows a still (the poster, or the video's first frame). Point at it and the video plays, muted and looping, while a 2px white hairline along the bottom edge grows with the loop. Leave and it pauses on the frame it reached; there's no jump back to the poster. Come back and it carries on from there. The optional timecode in the corner counts the seconds. Keyboard focus on the card, or on the link the card sits in, plays it too. On touch screens, where there's no hover, it plays while at least 60% of it is on screen and pauses when you scroll past. Under reduced motion it never plays by itself. While paused it requests no animation frames.

## Before you write code
1. **No dependencies.** It's one Client Component, with inline styles.
2. **The components folder.** Read `tsconfig.json` (or `jsconfig.json`) `compilerOptions.paths` and put the file wherever `@/components/...` resolves: `components/ui/` at the root, or `src/components/ui/`. In a JavaScript project, save it as `HoverVideo.jsx` and drop the types.
3. **The video.** Export a short loop (4 to 10s) without audio, sized to the card (about 1280px wide is plenty), as **MP4 (H.264)**. Put it in `public/`. A browser plays the first source it says it can play, and only moves to the next one on an error, never on a stall. So list the MP4 first; it decodes in every current browser. A WebM is optional, and goes second.
4. **The poster.** A JPEG of the frame you want at rest. Always give one: without it, what shows at rest varies by browser (a first frame in some, black in others).
5. **Links.** To make the card a link, wrap it in `<a>` or `<Link>`. The keyboard focus then lands on the link and still plays the video.

## Build

### 1. The component: `components/ui/HoverVideo.tsx`
```tsx
"use client";

import { useEffect, useRef, type CSSProperties } from "react";

type Source = { src: string; type?: string };

/**
 * A video card that holds a still until you point at it, then plays. A hairline along the bottom shows where
 * the loop is. Leave and it pauses on the frame it reached: no jump back to the poster.
 * Mouse: plays on hover. Keyboard: plays while the card (or the link around it) has keyboard focus.
 * Touch: plays while most of it is on screen. Reduced motion: never plays by itself.
 */
export default function HoverVideo({
  src,
  poster,
  label,
  ratio = "4 / 3",
  showTime = false,
  className,
  style,
}: {
  /** one URL, or several sources (e.g. WebM and MP4) */
  src: string | Source[];
  poster?: string;
  /** what the video shows, for screen readers */
  label: string;
  ratio?: string;
  /** a small timecode in the corner */
  showTime?: boolean;
  className?: string;
  style?: CSSProperties;
}) {
  const wrap = useRef<HTMLDivElement>(null);
  const video = useRef<HTMLVideoElement>(null);
  const bar = useRef<HTMLDivElement>(null);
  const time = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const el = wrap.current!;
    const v = video.current!;
    let raf = 0;
    // the hairline and the timecode only update while the video plays: a paused card costs nothing
    const draw = () => {
      if (v.duration) {
        bar.current!.style.transform = `scaleX(${(v.currentTime / v.duration).toFixed(4)})`;
        if (time.current) time.current.textContent = `00:${String(Math.floor(v.currentTime)).padStart(2, "0")}`;
      }
      raf = requestAnimationFrame(draw);
    };
    const onPlaying = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(draw);
    };
    const onPause = () => cancelAnimationFrame(raf);
    v.addEventListener("playing", onPlaying);
    v.addEventListener("pause", onPause);
    const play = () => {
      v.play().catch(() => {}); // a refused play (data saver, low power) just leaves the still
    };
    const pause = () => v.pause();
    const cleanups: (() => void)[] = [];

    if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      if (window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
        const enter = (e: PointerEvent) => e.pointerType !== "touch" && play();
        const leave = (e: PointerEvent) => e.pointerType !== "touch" && pause();
        el.addEventListener("pointerenter", enter);
        el.addEventListener("pointerleave", leave);
        cleanups.push(() => {
          el.removeEventListener("pointerenter", enter);
          el.removeEventListener("pointerleave", leave);
        });
        // the keyboard: the card itself, or the link it sits in, takes focus
        const focusable = (el.closest("a, button, [tabindex]") as HTMLElement | null) ?? el;
        const onFocus = (e: FocusEvent) => (e.target as HTMLElement).matches(":focus-visible") && play();
        const onBlur = (e: FocusEvent) => !focusable.contains(e.relatedTarget as Node) && !el.matches(":hover") && pause();
        focusable.addEventListener("focusin", onFocus);
        focusable.addEventListener("focusout", onBlur);
        cleanups.push(() => {
          focusable.removeEventListener("focusin", onFocus);
          focusable.removeEventListener("focusout", onBlur);
        });
      } else {
        // touch screens have no hover: play while most of the card is in view
        const io = new IntersectionObserver((entries) => (entries[0].intersectionRatio >= 0.6 ? play() : pause()), { threshold: [0, 0.6] });
        io.observe(el);
        cleanups.push(() => io.disconnect());
      }
    }
    return () => {
      cleanups.forEach((c) => c());
      v.removeEventListener("playing", onPlaying);
      v.removeEventListener("pause", onPause);
      cancelAnimationFrame(raf);
      v.pause();
    };
  }, []);

  const sources: Source[] = typeof src === "string" ? [{ src }] : src;
  return (
    <div ref={wrap} className={className} style={{ position: "relative", aspectRatio: ratio, overflow: "hidden", background: "#000", ...style }}>
      <video
        ref={video}
        poster={poster}
        muted
        loop
        playsInline
        preload="metadata"
        disablePictureInPicture
        aria-label={label}
        style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", display: "block" }}
      >
        {sources.map((s) => (
          <source key={s.src} src={s.src} type={s.type} />
        ))}
      </video>
      <div ref={bar} aria-hidden="true" style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: 2, background: "#fff", transformOrigin: "0 50%", transform: "scaleX(0)" }} />
      {showTime && (
        <span ref={time} aria-hidden="true" style={{ position: "absolute", right: 10, bottom: 10, fontSize: 12, color: "#fff", fontVariantNumeric: "tabular-nums", mixBlendMode: "difference" }}>
          00:00
        </span>
      )}
    </div>
  );
}
```

### 2. Use it
```tsx
import Link from "next/link";
import HoverVideo from "@/components/ui/HoverVideo";

<Link href="/houses/harlan">
  <HoverVideo
    src={[
      { src: "/video/harlan.mp4", type: "video/mp4" },
      { src: "/video/harlan.webm", type: "video/webm" },
    ]}
    poster="/video/harlan.jpg"
    label="Walkthrough of Harlan House at dusk"
    ratio="4 / 3"
  />
</Link>
```

## Why these values
- **Pause on the frame it reached, and resume from it:** the card remembers where you left it, so the next hover continues the walkthrough instead of replaying the opening. Jumping back to the poster flashes on every leave.
- **Muted and `playsInline`:** browsers only let a page start a video without a click or tap if it's muted, and a pointer entering a card isn't a click. `playsInline` keeps iOS from opening it full screen.
- **`preload="metadata"`:** the grid loads each clip's size and first frame, not the whole file, until someone points at it.
- **The hairline and timecode update only while it plays:** the animation loop starts on `playing` and stops on `pause`, so a page of paused cards costs nothing.
- **On touch, play at 60% in view:** a phone has no hover, so the card plays when it's the thing you're looking at. Below 60% it pauses, so only one or two play at once while you scroll.

## Failure patterns to avoid
Measured on Next.js 16.3.8 and React 19.2.8 in Chromium 153, Firefox 155 and WebKit 26.6 (Playwright 1.63), 2026-10-05:
- **WebM listed first.** Playwright's WebKit build on Windows said "probably" to VP9 WebM, then never loaded it: no frames after 5s, and no error. Because there was no error, it never fell back to the MP4, and the stalled video held the page's `load` event. With the MP4 first, all three engines played. That's one engine build, not Safari itself, but the rule holds for every browser: it only moves to the next source on an error.
- **A frame loop that keeps running while paused.** With the loop left on at pause, one paused card requested 61 frames a second in Chromium and WebKit and 165 in Firefox. The loop starts on `playing` and stops on `pause`.
- **No `muted`.** In Chromium's mobile emulation the unmuted `play()` was refused, and the card never played on touch. Playwright's desktop browsers allow unmuted autoplay, so the desktop case isn't measured here. Chrome's published policy (developer.chrome.com/blog/autoplay) allows sound only after the visitor has interacted with the site, and a hover isn't an interaction.

## Verify before you finish
Run each check, fix anything that fails, and say which ones you ran:
1. `npx tsc --noEmit` and `npm run build` both succeed.
2. At rest, the card shows its poster and is paused.
3. Point at it: it plays and the hairline grows. Leave: it pauses on that frame. Point again: it carries on from there.
4. Tab to the card (or its link): it plays; Tab away: it pauses.
5. In device emulation (touch), it plays while in view and pauses when scrolled away.
6. With `prefers-reduced-motion: reduce` emulated, pointing at it doesn't play it.
7. In Safari, the video plays (check that the MP4 is listed first).
