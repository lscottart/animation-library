"use client";
import { useState } from "react";
import Link from "next/link";
import SplitReveal from "@/components/ui/SplitReveal";
import ExposeGsap from "@/components/test/ExposeGsap";

// After the reveal, React must still own the text: links route client-side, handlers fire, updates land.
export default function Page() {
  const [n, setN] = useState(0);
  const [on, setOn] = useState(false);
  const [clicks, setClicks] = useState(0);
  return (
    <main style={{ padding: "8vh 6vw", maxWidth: 900, fontSize: 24 }}>
      <ExposeGsap />
      <SplitReveal id="links" trigger="load">
        Read the <Link id="nextlink" href="/tuned/roll">roll link notes</Link> or press{" "}
        <a id="handler" href="#" onClick={(e) => { e.preventDefault(); setClicks((c) => c + 1); }}>this handler</a> to count.
      </SplitReveal>
      <SplitReveal id="dyn" trigger="load">
        {n} items in a sentence long enough to wrap onto a second line at this width, count {n}.
      </SplitReveal>
      <SplitReveal id="struct" trigger="load">
        The state is {on ? <em>on</em> : "off"} right now.
      </SplitReveal>
      <p id="clicks">{clicks}</p>
      <button id="inc" onClick={() => setN((v) => v + 1)}>inc</button>
      <button id="toggle" onClick={() => setOn((v) => !v)}>toggle</button>
      <div style={{ height: "130vh" }} />
      {/* below the fold, narrow, so the link spans several lines and SplitText copies it per line */}
      <SplitReveal id="spanning" style={{ maxWidth: 360 }}>
        Before the link, <Link href="/tuned/list" className="span-link">a link long enough that it has to break across several lines of this column</Link> and after it.
      </SplitReveal>
      <div style={{ height: "60vh" }} />
    </main>
  );
}
