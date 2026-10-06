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
