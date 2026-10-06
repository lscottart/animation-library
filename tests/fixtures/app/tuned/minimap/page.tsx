import NoteMinimap from "@/components/ui/NoteMinimap";

// Release-test fixture for /animations:note-minimap: six sections (the rail shows five), one without a thumbnail
const tone = (g: number) => `data:image/svg+xml,${encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" width="72" height="40"><rect width="72" height="40" fill="rgb(${g},${g},${g})"/></svg>`)}`;
const SECTIONS = ["Harlan House", "Low Meadow", "Coldwater", "Sorrel Ridge", "Quarry House", "Sixth section"];

export default function Page() {
  return (
    <main id="note" style={{ maxWidth: 720, margin: "0 auto", padding: "120px 24px 60vh", fontSize: 18, lineHeight: 1.5, background: "#f2f2f2" }}>
      <NoteMinimap scope="#note" />
      <h1 style={{ fontSize: 56, margin: "0 0 80px" }}>Five houses</h1>
      {SECTIONS.map((name, i) => (
        <section key={name} id={`s${i + 1}`} data-minimap="" data-label={name} data-thumb={i === 2 ? undefined : tone(60 + i * 30)} style={{ marginBottom: 160 }}>
          <h2 style={{ fontSize: 36, margin: "0 0 16px" }}>{name}</h2>
          {Array.from({ length: 6 }, (_, k) => (
            <p key={k}>Section {i + 1}, paragraph {k + 1}. The rail follows the reading line on a soft spring and the corner marks lock onto the card for this section.</p>
          ))}
        </section>
      ))}
    </main>
  );
}
