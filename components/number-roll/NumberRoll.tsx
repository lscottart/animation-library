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
