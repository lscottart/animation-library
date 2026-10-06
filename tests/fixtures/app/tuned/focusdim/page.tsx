import FocusDim from "@/components/ui/FocusDim";

// Release-test fixture for /animations:focus-dim
const TILES = ["a", "b", "c", "d"];
const NAMES = ["Harlan House", "Low Meadow", "Coldwater"];

export default function Page() {
  return (
    <main style={{ padding: 60, background: "#f2f2f2", minHeight: "100vh" }}>
      <FocusDim style={{ display: "grid", gridTemplateColumns: "repeat(4, 200px)", gap: 24 }}>
        {TILES.map((k) => (
          <a key={k} id={`t-${k}`} href={`#${k}`} style={{ display: "block", height: 160, background: "#5a5f66", color: "#fff", padding: 12 }}>
            {k}
          </a>
        ))}
      </FocusDim>
      <FocusDim as="ul" dim={0.4} grayscale={false} style={{ listStyle: "none", padding: 0, margin: "60px 0 0", fontSize: 40 }}>
        {NAMES.map((n, i) => (
          <li key={n} id={`n-${i}`}>
            <a href={`#n${i}`} style={{ color: "#17191a", textDecoration: "none" }}>
              {n}
            </a>
          </li>
        ))}
      </FocusDim>
      <p style={{ marginTop: 60 }}>
        <a id="after" href="#after">After</a>
      </p>
    </main>
  );
}
