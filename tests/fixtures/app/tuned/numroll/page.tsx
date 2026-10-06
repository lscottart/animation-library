"use client";

import { useState } from "react";
import NumberRoll from "@/components/ui/NumberRoll";

// Release-test fixture for /animations:number-roll
export default function Page() {
  const [time, setTime] = useState("4:38 PM");
  const [n, setN] = useState("9");
  return (
    <main style={{ padding: 60, background: "#f2f2f2", fontSize: 18 }}>
      <div style={{ fontSize: 96, lineHeight: 1 }}>
        <NumberRoll value={time} className="t-top" /> <span className="ref">0</span>
      </div>
      <p>
        <button id="next" type="button" onClick={() => setTime("5:14 PM")}>
          Next house
        </button>{" "}
        <button id="grow" type="button" onClick={() => setN("10")}>
          Grow
        </button>{" "}
        <span style={{ fontSize: 40 }}>
          <NumberRoll value={n} className="t-len" />
        </span>
      </p>
      <div style={{ height: "160vh" }} />
      <div style={{ fontSize: 120, lineHeight: 1 }}>
        <NumberRoll value="1,284" className="t-below" />
      </div>
      <div style={{ height: "60vh" }} />
    </main>
  );
}
