"use client";

import { useState } from "react";
import ScrollColorFill from "@/components/ui/ScrollColorFill";

// Release-test fixture for /animations:scroll-color-fill
const LONG = "Before we draw anything, we stand on the land at dusk, mark where the last sun falls, and design every room to answer it.";
// Ü, a decomposed é (e + U+0301), a ZWJ emoji with a skin tone, and a flag: each must fill as one character
const GRAPHEMES = "Über cafe\u0301 \u{1F469}\u{1F3FD}‍\u{1F4BB} \u{1F1E8}\u{1F1ED}";

export default function Page() {
  const [text, setText] = useState("Every photograph here was taken in that hour.");
  return (
    <main style={{ padding: "0 60px", background: "#f2f2f2", fontSize: 44, lineHeight: 1.1 }}>
      <div style={{ height: "100vh" }} />
      <div style={{ maxWidth: 760 }}>
        <ScrollColorFill>{LONG}</ScrollColorFill>
      </div>
      <div style={{ height: "60vh" }} />
      <ScrollColorFill as="h2" style={{ fontSize: 56 }}>
        {GRAPHEMES}
      </ScrollColorFill>
      <div style={{ height: "60vh" }} />
      <button id="swap" type="button" onClick={() => setText("The text changed, and it still fills.")} style={{ fontSize: 16 }}>
        Swap text
      </button>
      <div style={{ maxWidth: 760 }}>
        <ScrollColorFill>{text}</ScrollColorFill>
      </div>
      <div style={{ height: "120vh" }} />
    </main>
  );
}
