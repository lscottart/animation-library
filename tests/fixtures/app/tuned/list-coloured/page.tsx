import "./dark.css";
import SlidingFillList from "@/components/ui/SlidingFillList";

const items = [
  { label: "Typography Principles (2019)", href: "#a" },
  { label: "Colors Combinations (2020)", href: "#b" },
  { label: "A very long project title that should truncate before it ever pushes the arrow out of the row", href: "#c" },
];

export default function Page() {
  return (
    <section style={{ background: "#17191a", color: "#f2f2f2", padding: "80px", fontSize: 24 }}>
      <SlidingFillList items={items} className="on-dark" />
    </section>
  );
}
