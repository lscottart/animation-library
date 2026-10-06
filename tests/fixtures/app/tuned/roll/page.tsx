import RollLink from "@/components/ui/RollLink";

const NAV_ITEMS = ["Work", "About", "Services", "Contact"];

// Ü, a decomposed é (e + U+0301), a ZWJ emoji with a skin tone, and a flag: each must roll as one letter
const GRAPHEMES = "Über café \u{1F469}\u{1F3FD}‍\u{1F4BB} \u{1F1E8}\u{1F1ED}";

export default function Page() {
  return (
    <main style={{ padding: 60, fontSize: 32 }}>
      <nav id="nav" style={{ display: "flex", gap: 24 }}>
        {NAV_ITEMS.map((item) => (
          <RollLink key={item} href={`/${item.toLowerCase()}`}>
            {item}
          </RollLink>
        ))}
      </nav>
      <p style={{ marginTop: 40 }}><RollLink href="/long">A much longer link label of thirty characters</RollLink></p>
      <p style={{ marginTop: 40, fontSize: 48 }}><RollLink id="desc" href="/g">Typography, glyphs</RollLink></p>
      <p style={{ marginTop: 40 }}><RollLink href="#tap">Tap target</RollLink></p>
      <p style={{ marginTop: 40 }}><RollLink id="emoji" href="#e">{GRAPHEMES}</RollLink></p>
    </main>
  );
}
