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
