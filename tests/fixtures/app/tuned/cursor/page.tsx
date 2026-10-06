import CursorLabel from "@/components/ui/CursorLabel";

// Release-test fixture for /animations:cursor-label
const TILE = { display: "block", height: 220 } as const;

export default function Page() {
  return (
    <main style={{ padding: 40, minHeight: "300vh", background: "#f2f2f2" }}>
      <CursorLabel />
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 300px)", gap: 40 }}>
        <a id="a" href="#a" data-cursor-label="(View house)" style={{ ...TILE, background: "#333" }}>
          <span style={{ display: "block", padding: 12, color: "#fff" }}>Harlan House</span>
        </a>
        <a id="b" href="#b" data-cursor-label="(View model)" style={{ ...TILE, background: "#ddd" }} />
        <div id="c" data-cursor-label="(Play)" style={{ ...TILE, background: "#666" }} />
      </div>
      {/* two labelled tiles that touch: a direct jump with no gap between them */}
      <div style={{ display: "flex", marginTop: 40 }}>
        <div id="d" data-cursor-label="(View drawing)" style={{ width: 300, height: 160, background: "#444" }} />
        <div id="e" data-cursor-label="(View photo)" style={{ width: 300, height: 160, background: "#999" }} />
      </div>
      <div id="plain" style={{ height: 220, marginTop: 40, background: "#ccc" }} />
    </main>
  );
}
