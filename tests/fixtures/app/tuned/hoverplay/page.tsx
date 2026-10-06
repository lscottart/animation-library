import HoverVideo from "@/components/ui/HoverVideo";

// Release-test fixture for /animations:hover-play
// MP4 first: a browser takes the first source it says it can play and only falls back on an error, not a stall
const SRC = [
  { src: "/tuned/clip.mp4", type: "video/mp4" },
  { src: "/tuned/clip.webm", type: "video/webm" },
];

export default function Page() {
  return (
    <main style={{ padding: 60, background: "#f2f2f2" }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 420px)", gap: 40 }}>
        <a id="card1" href="#card1" style={{ display: "block" }}>
          <HoverVideo src={SRC} poster="/tuned/clip.jpg" label="Kelvin ribbon study" className="v1" />
        </a>
        <HoverVideo src={SRC} poster="/tuned/clip.jpg" label="Second study" showTime className="v2" />
      </div>
      <div style={{ height: "160vh" }} />
      <HoverVideo src={SRC} poster="/tuned/clip.jpg" label="Third study" className="v3" style={{ width: 420 }} />
      <div style={{ height: "80vh" }} />
    </main>
  );
}
