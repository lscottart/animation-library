import SplitReveal from "@/components/ui/SplitReveal";
import ExposeGsap from "@/components/test/ExposeGsap";

export default function Page() {
  return (
    <main style={{ padding: "6vh 6vw", maxWidth: 820 }}>
      <ExposeGsap />
      <SplitReveal as="h2" trigger="load" id="br" style={{ fontSize: 48, lineHeight: 1.05 }}>
        First line,<br />then a forced break, and a third line wraps on its own here.
      </SplitReveal>
      <SplitReveal trigger="load" id="emoji" style={{ fontSize: 24, marginTop: 32 }}>
        Emoji and accents survive: café, naïve, Zürich 🏛️ 👩🏽‍💻, and «guillemets» — with a dash.
      </SplitReveal>
      <SplitReveal trigger="load" id="longword" style={{ fontSize: 24, marginTop: 32, overflowWrap: "anywhere" }}>
        A long token: https://example.com/a/very/long/path/that/does/not/break/naturally/at/all/anywhere/soon
      </SplitReveal>
      <SplitReveal as="h3" trigger="load" id="center" style={{ fontSize: 40, textAlign: "center", marginTop: 32 }}>
        Centred headline text that wraps across two lines
      </SplitReveal>
      <SplitReveal trigger="load" id="rtl" dir="rtl" lang="he" style={{ fontSize: 28, marginTop: 32 }}>
        טקסט בעברית שנפרש על פני כמה שורות כדי לבדוק כיוון מימין לשמאל בתוך המסכה
      </SplitReveal>
      <ul style={{ marginTop: 32, paddingLeft: 24, listStyle: "disc" }}>
        <SplitReveal as="li" trigger="load" id="li" style={{ fontSize: 22 }}>A list item can be the element itself, bullet included, and it still reveals.</SplitReveal>
      </ul>
      <SplitReveal trigger="load" id="empty" style={{ marginTop: 32 }}>{""}</SplitReveal>
      <div style={{ height: "110vh" }} />
      <SplitReveal id="later" style={{ fontSize: 24 }}>
        Resized before it was ever revealed: this paragraph must re-split at the new width and still land as plain text.
      </SplitReveal>
    </main>
  );
}
