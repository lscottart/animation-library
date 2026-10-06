import WipeButton from "@/components/ui/WipeButton";

// Release-test fixture for /animations:wipe-button
export default function Page() {
  return (
    <main style={{ padding: 60, fontSize: 18, display: "grid", gap: 48, justifyItems: "start", background: "#f2f2f2", minHeight: "100vh" }}>
      <WipeButton id="login" href="#login">Log In</WipeButton>
      <WipeButton id="cta" href="#cta" preset="cta" rest="outline">Begin a house</WipeButton>
      <WipeButton id="down" href="#down" preset="cta" rest="outline" direction="down" radius="0">Book a call</WipeButton>
      <WipeButton id="btn" type="submit">Send</WipeButton>
      <div style={{ fontSize: 44 }}>
        <WipeButton id="big" href="#big">Start a project</WipeButton>
      </div>
      <a id="after" href="#after">After</a>
    </main>
  );
}
