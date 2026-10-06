"use client";

import { useEffect, useRef } from "react";
import gsap from "gsap";

// The trail: x catches up a little faster than y, so the label floats as it follows (Obys DES).
const X_LERP = 0.11;
const Y_LERP = 0.085;

type Props = {
  /** where the label sits relative to the pointer, in px */
  offsetX?: number;
  offsetY?: number;
  /** white with a difference blend inverts against whatever is under it, so it reads on photos and on paper */
  blend?: boolean;
  className?: string;
};

export default function CursorLabel({ offsetX = 18, offsetY = -10, blend = true, className }: Props) {
  const rootRef = useRef<HTMLDivElement>(null);
  const textRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    // Mouse and trackpad only. On touch there's no hover to label, and under reduced motion it stays off.
    const fine = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
    const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!fine || still) return;
    const root = rootRef.current!;
    const text = textRef.current!;
    const setX = gsap.quickSetter(root, "x", "px");
    const setY = gsap.quickSetter(root, "y", "px");
    const pos = { x: -200, y: -200 };
    const target = { x: -200, y: -200 };
    const pointer = { x: -1, y: -1 };
    gsap.set(text, { yPercent: 110 }); // the label waits below its window
    gsap.set(root, { x: pos.x, y: pos.y, visibility: "visible" });

    // The exit always finishes before the next entry (a direct jump between two labelled items queues the
    // second), and coming back to the same item mid-exit catches the roll instead of replaying it.
    let state: "hidden" | "shown" | "exiting" = "hidden";
    let shownFor: Element | null = null;
    let pending: Element | null = null;

    const enter = (item: Element) => {
      state = "shown";
      shownFor = item;
      pending = null;
      text.textContent = item.getAttribute("data-cursor-label") || "(View)";
      // appear where the pointer is, then roll in: no fly-in from the last spot
      pos.x = target.x;
      pos.y = target.y;
      setX(pos.x);
      setY(pos.y);
      gsap.killTweensOf(text);
      gsap.fromTo(text, { yPercent: 110 }, { yPercent: 0, duration: 0.4, ease: "expo.out" });
    };
    const exit = () => {
      state = "exiting";
      gsap.killTweensOf(text);
      gsap.to(text, {
        yPercent: -110,
        duration: 0.3,
        ease: "expo.out",
        onComplete: () => {
          state = "hidden";
          shownFor = null;
          if (pending) {
            const next = pending;
            pending = null;
            enter(next);
          }
        },
      });
    };
    const evaluate = (el: Element | null) => {
      const item = el ? el.closest("[data-cursor-label]") : null;
      if (state === "shown") {
        if (item === shownFor) return;
        if (item) pending = item;
        exit();
      } else if (state === "exiting") {
        if (item === shownFor) {
          state = "shown";
          pending = null;
          gsap.killTweensOf(text);
          gsap.to(text, { yPercent: 0, duration: 0.25, ease: "expo.out" });
        } else {
          pending = item; // the next item waits; null cancels the queue
        }
      } else if (item) {
        enter(item);
      }
    };

    const onMove = (e: PointerEvent) => {
      if (e.pointerType === "touch") return;
      pointer.x = e.clientX;
      pointer.y = e.clientY;
      target.x = e.clientX + offsetX;
      target.y = e.clientY + offsetY;
      evaluate(e.target as Element);
    };
    // Scrolling moves the page under a still pointer (smooth-scroll libraries send no pointer events), so check
    // again what's beneath it.
    const onScroll = () => {
      if (pointer.x >= 0) evaluate(document.elementFromPoint(pointer.x, pointer.y));
    };
    const onLeaveWindow = () => evaluate(null);
    const tick = () => {
      pos.x += (target.x - pos.x) * X_LERP;
      pos.y += (target.y - pos.y) * Y_LERP;
      setX(pos.x);
      setY(pos.y);
    };

    document.addEventListener("pointermove", onMove, { passive: true });
    window.addEventListener("scroll", onScroll, { passive: true });
    document.documentElement.addEventListener("mouseleave", onLeaveWindow);
    gsap.ticker.add(tick);
    return () => {
      document.removeEventListener("pointermove", onMove);
      window.removeEventListener("scroll", onScroll);
      document.documentElement.removeEventListener("mouseleave", onLeaveWindow);
      gsap.ticker.remove(tick);
      gsap.killTweensOf(text);
    };
  }, [offsetX, offsetY]);

  return (
    <div
      ref={rootRef}
      data-cursor-label-root=""
      aria-hidden="true"
      className={className}
      style={{
        position: "fixed",
        left: 0,
        top: 0,
        zIndex: 100,
        pointerEvents: "none",
        visibility: "hidden",
        whiteSpace: "nowrap",
        color: blend ? "#fff" : undefined,
        mixBlendMode: blend ? "difference" : undefined,
      }}
    >
      {/* the one-line window the label rolls through */}
      <span style={{ display: "block", overflow: "hidden", lineHeight: 1.3 }}>
        <span ref={textRef} style={{ display: "block" }}>
          (View)
        </span>
      </span>
    </div>
  );
}
