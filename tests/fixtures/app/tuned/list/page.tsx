import SlidingFillList from "@/components/ui/SlidingFillList";

const projects = [
  { label: "Typography Principles (2019)", href: "/work/typography" },
  { label: "Colors Combinations (2020)", href: "/work/colors" },
  { label: "Grids (2021)", href: "/work/grids" },
  { label: "Instagram", href: "https://instagram.com", external: true },
];

export default function Page() {
  return (
    <section style={{ background: "#f2f2f2", color: "#17191a", padding: "80px" }}>
      <SlidingFillList items={projects} />
    </section>
  );
}
