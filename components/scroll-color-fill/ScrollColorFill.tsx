"use client";

import { useRef, type CSSProperties, type ElementType } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useGSAP } from "@gsap/react";
import "./ScrollColorFill.css";

gsap.registerPlugin(ScrollTrigger, useGSAP);

// One span per user-perceived character, so an emoji or an accented letter fills as one piece.
// Intl.Segmenter is in Node and in every current browser, so the server and the browser split alike.
function characters(text: string): string[] {
  if (typeof Intl !== "undefined" && "Segmenter" in Intl) {
    return Array.from(new Intl.Segmenter(undefined, { granularity: "grapheme" }).segment(text), (s) => s.segment);
  }
  return Array.from(text);
}

type Props = {
  children: string;
  /** the element to render: p, h2, blockquote... */
  as?: ElementType;
  /** the colour before the fill, and the colour it fills to */
  from?: string;
  to?: string;
  /** where the fill starts and ends, as ScrollTrigger positions */
  start?: string;
  end?: string;
  className?: string;
  style?: CSSProperties;
};

export default function ScrollColorFill({
  children,
  as: Tag = "p",
  from = "#b4b6b8",
  to = "#17191a",
  start = "top 78%",
  end = "bottom 42%",
  className,
  style,
}: Props) {
  const root = useRef<HTMLElement>(null);
  // Split on the server, in React: React owns every span, so nothing rewrites the DOM behind its back.
  // Whitespace stays plain text between the words, so lines break exactly as they would without the effect.
  const parts = children.split(/(\s+)/).filter((w) => w !== "").map((w) => (/^\s+$/.test(w) ? w : characters(w)));

  useGSAP(
    () => {
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
      const chars = root.current!.querySelectorAll(".scf__ch");
      gsap.fromTo(chars, { color: from }, { color: to, ease: "none", stagger: 0.05, scrollTrigger: { trigger: root.current!, start, end, scrub: 0.4 } });
    },
    { scope: root, dependencies: [children, from, to, start, end], revertOnUpdate: true },
  );

  return (
    <Tag ref={root} className={["scf", className].filter(Boolean).join(" ")} style={{ "--scf-from": from, "--scf-to": to, ...style } as CSSProperties}>
      {parts.map((part, pi) =>
        typeof part === "string" ? (
          part
        ) : (
          // a word never breaks across lines: its letters stay together
          <span key={pi} className="scf__word">
            {part.map((ch, ci) => (
              <span key={ci} className="scf__ch">
                {ch}
              </span>
            ))}
          </span>
        ),
      )}
    </Tag>
  );
}
