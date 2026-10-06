"use client";
import { useState } from "react";
import SplitReveal from "@/components/ui/SplitReveal";
import ExposeGsap from "@/components/test/ExposeGsap";

export default function Page() {
  const [k, setK] = useState(0);
  const [on, setOn] = useState(true);
  return (
    <main style={{ padding: 40 }}>
      <ExposeGsap />
      <button id="remount" onClick={() => setK((v) => v + 1)}>remount</button>
      <button id="toggle" onClick={() => setOn((v) => !v)}>toggle</button>
      <div style={{ height: "150vh" }} />
      {on && (
        <div key={k}>
          {Array.from({ length: 8 }, (_, i) => (
            <SplitReveal key={i} className="churn" style={{ fontSize: 20, marginTop: 24, maxWidth: 520 }}>
              Paragraph {i + 1}: lines rise through masks, one after another, as the section scrolls into view.
            </SplitReveal>
          ))}
        </div>
      )}
    </main>
  );
}
