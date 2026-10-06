import "./nopad.css";
import SplitReveal from "@/components/ui/SplitReveal";
import ExposeGsap from "@/components/test/ExposeGsap";

export default function Page() {
  return (
    <main style={{ padding: "6vh 6vw", background: "#fff", color: "#000" }}>
      <ExposeGsap />
      <SplitReveal as="h2" trigger="load" id="lh085" style={{ fontSize: 96, lineHeight: 0.85, fontFamily: "inherit", fontWeight: 600, margin: "0 0 48px", maxWidth: 760 }}>
        Quietly gathering typography, glyphs and jumpy descenders
      </SplitReveal>
      <SplitReveal as="h2" trigger="load" id="lh1" style={{ fontSize: 72, lineHeight: 1.0, fontFamily: "inherit", fontWeight: 600, margin: "0 0 48px", maxWidth: 760 }}>
        Quietly gathering typography, glyphs and jumpy descenders
      </SplitReveal>
      <SplitReveal as="h2" trigger="load" id="lh12" style={{ fontSize: 40, lineHeight: 1.2, fontFamily: "inherit", fontWeight: 600, margin: "0 0 48px", maxWidth: 760 }}>
        Quietly gathering typography, glyphs and jumpy descenders
      </SplitReveal>
      <SplitReveal as="h2" trigger="load" id="lh15" style={{ fontSize: 18, lineHeight: 1.5, fontFamily: "inherit", fontWeight: 600, margin: "0 0 48px", maxWidth: 760 }}>
        Quietly gathering typography, glyphs and jumpy descenders
      </SplitReveal>
      <SplitReveal as="h2" trigger="load" id="serif" style={{ fontSize: 72, lineHeight: 0.95, fontFamily: "Georgia, 'Times New Roman', serif", fontWeight: 600, margin: "0 0 48px", maxWidth: 760 }}>
        Quietly gathering typography, glyphs and jumpy descenders
      </SplitReveal>
    </main>
  );
}
