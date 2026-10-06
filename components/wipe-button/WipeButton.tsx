"use client";

import Link from "next/link";
import { useEffect, useRef, type CSSProperties, type MouseEventHandler, type Ref } from "react";
import gsap from "gsap";

type Timing = { duration: number; ease: string };

// Measured frame by frame from des.obys.agency at 60 fps.
const PRESETS = {
  // the "Log In" button: the fill leaves in 221 ms (sine.in) and comes back in 207 ms (sine.out)
  login: { clear: { duration: 0.22, ease: "sine.in" }, cover: { duration: 0.21, ease: "sine.out" } },
  // the larger call-to-action: 500 ms in, 400 ms out, on expo.out (cubic-bezier(0.16, 1, 0.3, 1))
  cta: { clear: { duration: 0.4, ease: "expo.out" }, cover: { duration: 0.5, ease: "expo.out" } },
} satisfies Record<string, { clear: Timing; cover: Timing }>;

type WipeButtonProps = {
  children: string;
  /** with href it renders a Next.js Link; without, a <button> */
  href?: string;
  onClick?: MouseEventHandler<HTMLElement>;
  type?: "button" | "submit";
  target?: string;
  rel?: string;
  id?: string;
  className?: string;
  style?: CSSProperties;
  preset?: keyof typeof PRESETS;
  /** filled: solid at rest, hover clears it. outline: clear at rest, hover fills it. */
  rest?: "filled" | "outline";
  /** the one direction the fill ever travels */
  direction?: "up" | "down";
  ink?: string;
  paper?: string;
  radius?: string;
};

export default function WipeButton({
  children,
  href,
  onClick,
  type = "button",
  target,
  rel,
  id,
  className,
  style,
  preset = "login",
  rest = "filled",
  direction = "up",
  ink = "#17191a",
  paper = "#ffffff",
  radius = "0.45em",
}: WipeButtonProps) {
  const root = useRef<HTMLElement>(null);
  const panelA = useRef<HTMLSpanElement>(null);
  const panelB = useRef<HTMLSpanElement>(null);
  const label = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const el = root.current!;
    const panels = [panelA.current!, panelB.current!];
    const text = label.current!;
    const s = direction === "down" ? 1 : -1; // the sign of "forward" in yPercent
    const timing = PRESETS[preset];
    const still = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let active = 0;

    // A panel's forward progress: -101 waiting at the entry edge, 0 covering, 101 gone out the exit edge.
    const progress = (i: number) => (gsap.getProperty(panels[i], "yPercent") as number) * s;
    const place = (i: number, p: number) => gsap.set(panels[i], { yPercent: p * s });
    const move = (i: number, p: number, t: Timing) =>
      still() ? place(i, p) : gsap.to(panels[i], { yPercent: p * s, duration: t.duration, ease: t.ease, overwrite: true });
    const tint = (covered: boolean, t: Timing) =>
      gsap.to(text, { color: covered ? paper : ink, duration: still() ? 0 : t.duration, ease: t.ease, overwrite: true });

    // The server already parked the panels with a CSS transform. Hand that over to GSAP as yPercent and zero
    // the px offset GSAP parsed from it, or the two would add up.
    gsap.set(panels, { y: 0 });
    place(0, rest === "filled" ? 0 : -101);
    place(1, -101);

    const cover = () => {
      if (progress(active) <= 0) {
        move(active, 0, timing.cover); // still arriving, or waiting: keep coming forward
      } else {
        // the active panel is on its way out: let it go, and bring the other one in behind it
        active = 1 - active;
        place(active, -101);
        move(active, 0, timing.cover);
      }
      tint(true, timing.cover);
    };
    const clear = () => {
      move(active, 101, timing.clear); // always forward, out through the exit edge
      tint(false, timing.clear);
    };

    let hovered = false;
    let focused = false;
    let covered = rest === "filled";
    const sync = () => {
      const want = rest === "filled" ? !(hovered || focused) : hovered || focused;
      if (want === covered) return;
      covered = want;
      if (want) cover();
      else clear();
    };
    // Touch is ignored on purpose: a tap should just follow the link, not leave a half-wiped button behind.
    const enter = (e: PointerEvent) => {
      if (e.pointerType === "touch") return;
      hovered = true;
      sync();
    };
    const leave = (e: PointerEvent) => {
      if (e.pointerType === "touch") return;
      hovered = false;
      sync();
    };
    const focus = () => {
      focused = el.matches(":focus-visible"); // the keyboard, not the focus a mouse click leaves behind
      sync();
    };
    const blur = () => {
      focused = false;
      sync();
    };

    el.addEventListener("pointerenter", enter);
    el.addEventListener("pointerleave", leave);
    el.addEventListener("focus", focus);
    el.addEventListener("blur", blur);
    return () => {
      el.removeEventListener("pointerenter", enter);
      el.removeEventListener("pointerleave", leave);
      el.removeEventListener("focus", focus);
      el.removeEventListener("blur", blur);
      gsap.killTweensOf([...panels, text]);
    };
  }, [preset, rest, direction, ink, paper]);

  // Where each panel sits before JavaScript runs: so the first paint is already right.
  const waiting = `translateY(${direction === "down" ? "-101%" : "101%"})`;
  const panel: CSSProperties = { position: "absolute", inset: 0, background: ink, pointerEvents: "none" };
  const box: CSSProperties = {
    position: "relative",
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "0.75em 1.2em",
    border: `1.5px solid ${ink}`,
    borderRadius: radius,
    overflow: "hidden",
    isolation: "isolate",
    background: paper,
    color: ink,
    font: "inherit",
    lineHeight: 1,
    textDecoration: "none",
    cursor: "pointer",
    ...style,
  };
  const inner = (
    <>
      <span ref={panelA} aria-hidden="true" style={{ ...panel, transform: rest === "filled" ? undefined : waiting }} />
      <span ref={panelB} aria-hidden="true" style={{ ...panel, transform: waiting }} />
      <span ref={label} style={{ position: "relative", color: rest === "filled" ? paper : ink }}>
        {children}
      </span>
    </>
  );

  return href ? (
    <Link ref={root as Ref<HTMLAnchorElement>} href={href} id={id} className={className} style={box} target={target} rel={rel} onClick={onClick}>
      {inner}
    </Link>
  ) : (
    <button ref={root as Ref<HTMLButtonElement>} type={type} id={id} className={className} style={box} onClick={onClick}>
      {inner}
    </button>
  );
}
