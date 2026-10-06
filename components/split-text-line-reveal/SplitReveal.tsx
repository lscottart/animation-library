"use client";

import { useRef, type ComponentPropsWithoutRef, type ElementType } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { SplitText } from "gsap/SplitText";
import { useGSAP } from "@gsap/react";

gsap.registerPlugin(useGSAP, ScrollTrigger, SplitText);

// SplitText's revert() rebuilds the element from an HTML string, which swaps out the DOM nodes React rendered.
// React keeps editing the old ones, so links stop routing client-side, onClick stops firing, and the next change
// to the text crashes. This records React's nodes and returns a function that puts them back.
function keepReactNodes(root: Element) {
  const children = new Map<Element, ChildNode[]>();
  const texts = new Map<Text, string>();
  const record = (parent: Element) => {
    children.set(parent, Array.from(parent.childNodes));
    parent.childNodes.forEach((node) => {
      if (node.nodeType === Node.TEXT_NODE) texts.set(node as Text, (node as Text).data);
      else if (node.nodeType === Node.ELEMENT_NODE) record(node as Element);
    });
  };
  record(root);
  return () => {
    children.forEach((nodes, parent) => parent.replaceChildren(...nodes));
    texts.forEach((data, node) => (node.data = data)); // SplitText edits text nodes as it splits them
  };
}

// Moving the nodes drops keyboard focus, so put it back. A link that wraps was split into SplitText's copies
// (one per line) and React's original (the last line), so focus on a copy goes to the original.
function refocus(root: Element, focused: HTMLElement | null) {
  if (!focused || document.activeElement === focused) return;
  const target = root.contains(focused)
    ? focused
    : Array.from(root.querySelectorAll<HTMLElement>(focused.tagName)).find((n) =>
        n.cloneNode().isEqualNode(focused.cloneNode()),
      );
  target?.focus({ preventScroll: true });
}

type SplitRevealProps<T extends ElementType> = {
  /** The element to render: "h1", "p", "h2"… (default "p") */
  as?: T;
  /** "scroll": reveal when the element reaches `start`. "load": reveal as soon as it's ready. */
  trigger?: "scroll" | "load";
  delay?: number;
  duration?: number;
  stagger?: number;
  ease?: string;
  /** ScrollTrigger start, "element-edge viewport-edge" */
  start?: string;
} & Omit<ComponentPropsWithoutRef<T>, "as">;

export default function SplitReveal<T extends ElementType = "p">({
  as,
  trigger = "scroll",
  delay = 0,
  duration = 1,
  stagger = 0.1,
  ease = "power4.out",
  start = "top 90%",
  children,
  ...rest
}: SplitRevealProps<T>) {
  const Tag: ElementType = as ?? "p";
  const ref = useRef<HTMLElement>(null);

  useGSAP(
    (_context, contextSafe) => {
      const el = ref.current;
      if (!el) return;
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        gsap.set(el, { visibility: "visible" });
        return;
      }
      let live = true;
      let stop: (() => void) | undefined;
      // Created after an await, so it must run through contextSafe: that records the split, its tween and its
      // ScrollTrigger in this component's context, and unmounting reverts all three.
      const reveal = contextSafe!(() => {
        if (!live) return;
        let started = trigger === "scroll"; // a scroll reveal is started by its ScrollTrigger
        let tween: gsap.core.Tween | undefined;
        SplitText.create(el, {
          type: "lines",
          mask: "lines",
          linesClass: "split-line",
          autoSplit: true, // re-splits if the width changes or a font arrives before the reveal
          // aria "auto" labels the element and hides the lines, which would also hide any link inside it
          aria: el.querySelector("a, button, input, select, textarea, [tabindex]") ? "none" : "auto",
          onRevert: keepReactNodes(el), // after every revert, autoSplit's re-splits included
          onSplit(self) {
            // Each mask clips 0.3em beyond its line box (a clip-path, which changes no layout), so tight leading
            // never cuts descenders or accents, and each line starts that much further down, so nothing peeks out.
            const room = 0.3 * parseFloat(getComputedStyle(el).fontSize);
            (self.masks as HTMLElement[]).forEach((mask) => {
              mask.style.overflow = "visible";
              mask.style.clipPath = `inset(-${room}px -1em -${room}px -1em)`;
            });
            tween = gsap.from(self.lines, {
              y: (_i: number, line: HTMLElement) => line.offsetHeight + 2 * room,
              duration,
              stagger,
              ease,
              delay,
              paused: !started,
              scrollTrigger: trigger === "scroll" ? { trigger: el, start, once: true } : undefined,
              onComplete: () => {
                const focused = el.contains(document.activeElement) ? (document.activeElement as HTMLElement) : null;
                self.revert(); // plain text again: reflows on resize, reads normally
                refocus(el, focused);
              },
            });
            gsap.set(el, { visibility: "visible" }); // the CSS hid it until the lines were below their masks
            return tween; // returned so autoSplit can re-split and carry the progress over
          },
        });
        if (!started) {
          // GSAP times a new tween from the last frame it rendered, so main-thread work since then (hydration, a
          // WebGL scene starting up) would cut off the start of the motion. Start it on the second frame instead: the
          // first still has to lay out and paint the split lines (many lines, fallback fonts), which can take longer
          // than a frame, and that time would count as motion too.
          let ticks = 0;
          const go = () => {
            if (++ticks < 2) return;
            gsap.ticker.remove(go);
            started = true;
            if (live) tween?.play();
          };
          gsap.ticker.add(go);
          stop = () => gsap.ticker.remove(go);
        }
      });
      document.fonts.ready.then(reveal); // split with the final font's line breaks
      return () => {
        live = false;
        stop?.();
      };
    },
    { scope: ref, dependencies: [trigger, delay, duration, stagger, ease, start] },
  );

  return (
    <Tag ref={ref} data-split-reveal="" {...rest}>
      {children}
    </Tag>
  );
}
