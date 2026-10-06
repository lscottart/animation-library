"use client";
import { useState } from "react";
import SplitReveal from "@/components/ui/SplitReveal";

// test-only: the text changes while it is still split, waiting below the fold (key)
export default function Page() {
  const [on, setOn] = useState(false);
  return (
    <main style={{ padding: "8vh 6vw", maxWidth: 900, fontSize: 24 }}>
      <button id="t" onClick={() => setOn((v) => !v)}>toggle</button>
      <div style={{ height: "130vh" }} />
      <SplitReveal id="dyn" key={String(on)}>
        The state is {on ? <em>on</em> : "off"} right now, in a sentence long enough to wrap at this width.
      </SplitReveal>
      <div style={{ height: "40vh" }} />
    </main>
  );
}
