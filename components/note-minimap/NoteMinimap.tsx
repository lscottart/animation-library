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
