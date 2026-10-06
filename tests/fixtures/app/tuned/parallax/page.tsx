import Image from "next/image";
import ParallaxImage from "@/components/ui/ParallaxImage";

// Release-test fixture for /animations:parallax-image: drift with <img>, zoom with next/image, settle
export default function Page() {
  return (
    <main style={{ padding: "0 80px", background: "#f2f2f2" }}>
      <div style={{ height: "100vh" }} />
      <ParallaxImage mode="drift" ratio="16 / 10" style={{ width: 720 }}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img id="drift-img" src="/tuned/house.svg" alt="Drift" />
      </ParallaxImage>
      <div style={{ height: "80vh" }} />
      <ParallaxImage mode="zoom" ratio="4 / 3" style={{ width: 640 }}>
        <Image src="/tuned/house.svg" alt="Zoom" fill unoptimized sizes="640px" />
      </ParallaxImage>
      <div style={{ height: "80vh" }} />
      <ParallaxImage mode="settle" ratio="4 / 3" style={{ width: 640 }}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/tuned/house.svg" alt="Settle" />
      </ParallaxImage>
      <div style={{ height: "120vh" }} />
    </main>
  );
}
