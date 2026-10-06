import SplitReveal from "@/components/ui/SplitReveal";
import ExposeGsap from "@/components/test/ExposeGsap";
import Busy from "./Busy";

export default async function Page({ searchParams }: { searchParams: Promise<{ busy?: string; delay?: string }> }) {
  const { busy, delay } = await searchParams;
  return (
    <main style={{ padding: "6vh 6vw", maxWidth: 820 }}>
      <ExposeGsap />
      <Busy ms={Number(busy ?? 0)} />
      <SplitReveal as="h2" trigger="load" delay={Number(delay ?? 0)} id="br" style={{ fontSize: 48, lineHeight: 1.05 }}>
        First line,<br />then a forced break, and a third line wraps on its own here.
      </SplitReveal>
    </main>
  );
}
