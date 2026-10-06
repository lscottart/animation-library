import Link from "next/link";
import type { ComponentProps, CSSProperties } from "react";
import "./RollLink.css";

type RollLinkProps = Omit<ComponentProps<typeof Link>, "children"> & { children: string };

// One span per user-perceived character, so an emoji or an accented letter rolls as one piece.
// Intl.Segmenter is in Node and in every current browser, so the server and the browser split alike.
function characters(text: string): string[] {
  if (typeof Intl !== "undefined" && "Segmenter" in Intl) {
    return Array.from(new Intl.Segmenter(undefined, { granularity: "grapheme" }).segment(text), (s) => s.segment);
  }
  return Array.from(text);
}

export default function RollLink({ children, className, ...rest }: RollLinkProps) {
  return (
    <Link aria-label={children} {...rest} className={["roll-link", className].filter(Boolean).join(" ")}>
      <span className="roll-window">
        {characters(children).map((ch, i) => (
          <span key={i} className="roll-letter" data-ch={ch} style={{ "--i": i } as CSSProperties}>
            {ch}
          </span>
        ))}
      </span>
    </Link>
  );
}
