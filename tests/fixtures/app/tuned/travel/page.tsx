import { TravellingNav, TravellingTooltip } from "@/components/ui/TravellingIndicator";

// Release-test fixture for /animations:travelling-indicator
const NAV = ["Houses", "Studio", "Process", "Journal", "Contact"].map((label) => ({ label, href: `#${label.toLowerCase()}` }));
const icon = (d: string) => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.3" aria-hidden="true">
    <path d={d} />
  </svg>
);
const TOOLS = [
  { label: "Share", icon: icon("M5 11v4h10v-4 M10 3v9 M6.5 6.5 10 3l3.5 3.5") },
  { label: "Download", icon: icon("M5 15h10 M10 3v9 M6.5 8.5 10 12l3.5-3.5") },
  { label: "Add to collection", icon: icon("M10 4v12 M4 10h12") },
  { label: "Email", icon: icon("M3.5 5.5h13v9h-13z M3.5 5.5 10 11l6.5-5.5") },
];

export default function Page() {
  return (
    <main style={{ padding: 60, fontSize: 22, background: "#f2f2f2", minHeight: "100vh", display: "grid", gap: 70, justifyItems: "start", alignContent: "start" }}>
      <div id="block">
        <TravellingNav items={NAV} current="#studio" />
      </div>
      <div id="under" style={{ fontSize: 18 }}>
        <TravellingNav items={NAV} current="#houses" variant="underline" label="Filters" />
      </div>
      <div id="none">
        <TravellingNav items={NAV} label="Unselected" />
      </div>
      <div id="tools">
        <TravellingTooltip items={TOOLS} />
      </div>
      <a id="after" href="#after">After</a>
    </main>
  );
}
