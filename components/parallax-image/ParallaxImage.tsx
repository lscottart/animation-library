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
