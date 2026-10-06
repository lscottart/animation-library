import type { CSSProperties, ElementType, ReactNode } from "react";
import "./FocusDim.css";

/**
 * Hover (or keyboard-focus) one child and its siblings step back. Pure CSS, a Server Component.
 * Every direct child is an item: a card, a list row, a logo, a link.
 */
export default function FocusDim({
  children,
  as: Tag = "div",
  dim = 0.25,
  grayscale = true,
  className,
  style,
}: {
  children: ReactNode;
  as?: ElementType;
  /** the siblings' opacity while one item has focus */
  dim?: number;
  /** also drain the siblings' colour (for images) */
  grayscale?: boolean;
  className?: string;
  style?: CSSProperties;
}) {
  return (
    <Tag
      className={["focus-dim", className].filter(Boolean).join(" ")}
      style={{ "--fd-dim": dim, "--fd-filter": grayscale ? "grayscale(1)" : "none", ...style } as CSSProperties}
    >
      {children}
    </Tag>
  );
}
