import SplitReveal from "@/components/ui/SplitReveal";
import ExposeGsap from "@/components/test/ExposeGsap";

export default async function Page({ searchParams }: { searchParams: Promise<{ only?: string }> }) {
  const { only } = await searchParams;
  return (
    <main style={{ padding: "6vh 6vw", background: "#fff", color: "#000" }}>
      <ExposeGsap />
      {(!only || only === "lh085") && <SplitReveal as="h2" trigger="load" id="lh085" style={{ fontSize: 96, lineHeight: 0.85, fontFamily: "inherit", fontWeight: 600, margin: "0 0 48px", maxWidth: 760 }}>
        Quietly gathering typography, glyphs and jumpy descenders
      </SplitReveal>}
      {(!only || only === "lh1") && <SplitReveal as="h2" trigger="load" id="lh1" style={{ fontSize: 72, lineHeight: 1.0, fontFamily: "inherit", fontWeight: 600, margin: "0 0 48px", maxWidth: 760 }}>
        Quietly gathering typography, glyphs and jumpy descenders
      </SplitReveal>}
      {(!only || only === "lh12") && <SplitReveal as="h2" trigger="load" id="lh12" style={{ fontSize: 40, lineHeight: 1.2, fontFamily: "inherit", fontWeight: 600, margin: "0 0 48px", maxWidth: 760 }}>
        Quietly gathering typography, glyphs and jumpy descenders
      </SplitReveal>}
      {(!only || only === "lh15") && <SplitReveal as="h2" trigger="load" id="lh15" style={{ fontSize: 18, lineHeight: 1.5, fontFamily: "inherit", fontWeight: 600, margin: "0 0 48px", maxWidth: 760 }}>
        Quietly gathering typography, glyphs and jumpy descenders
      </SplitReveal>}
      {(!only || only === "serif") && <SplitReveal as="h2" trigger="load" id="serif" style={{ fontSize: 72, lineHeight: 0.95, fontFamily: "Georgia, 'Times New Roman', serif", fontWeight: 600, margin: "0 0 48px", maxWidth: 760 }}>
        Quietly gathering typography, glyphs and jumpy descenders
      </SplitReveal>}
    </main>
  );
}
