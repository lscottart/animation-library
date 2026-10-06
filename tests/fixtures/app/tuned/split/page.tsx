import SplitReveal from "@/components/ui/SplitReveal";
import ExposeGsap from "@/components/test/ExposeGsap";

export default function Page() {
  return (
    <main style={{ padding: "8vh 6vw", maxWidth: 900 }}>
      <ExposeGsap />
      <SplitReveal as="h1" trigger="load" delay={0.2} id="hero" style={{ fontSize: 72, lineHeight: 1, fontWeight: 600 }}>
        Glyphs hang, typography lands.
      </SplitReveal>
      <SplitReveal id="p1" delay={0.1} style={{ fontSize: 22, marginTop: 40 }}>
        Every house is drawn around one moment: the first lamp, the last light, the view back from the drive. A small studio in the hills outside Ember Hollow; we stand on the land at dusk before we draw anything at all.
      </SplitReveal>
      <SplitReveal id="nested" style={{ fontSize: 22, marginTop: 40 }}>
        Text with <a href="/next" id="inlink" style={{ textDecoration: "underline" }}>a link that spans words</a>, some <em>emphasis</em> and <strong>strong text</strong> in the middle of a sentence that wraps.
      </SplitReveal>
      <div style={{ height: "120vh" }} />
      <SplitReveal id="below" style={{ fontSize: 22 }}>
        This paragraph sits below the fold and should rise only when it is scrolled into view, quietly, line by line.
      </SplitReveal>
      <div id="after-below" style={{ height: 40 }} />
    </main>
  );
}
