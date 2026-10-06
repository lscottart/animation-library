"use client";
import { useLayoutEffect } from "react";

// test-only: blocks the main thread for `ms` right after #br is split, the way a WebGL scene or a
// heavy hydration does on a real site, before the reveal's first frame can render
export default function Busy({ ms }: { ms: number }) {
  useLayoutEffect(() => {
    if (!ms) return;
    const el = document.getElementById("br");
    if (!el) return;
    const mo = new MutationObserver(() => {
      if (!el.querySelector(".split-line")) return;
      mo.disconnect();
      const end = performance.now() + ms;
      while (performance.now() < end) {}
    });
    mo.observe(el, { childList: true, subtree: true });
    return () => mo.disconnect();
  }, [ms]);
  return null;
}
