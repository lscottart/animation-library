import Link from "next/link";
import "./SlidingFillList.css";

export type SlidingFillItem = {
  label: string;
  href: string;
  /** opens in a new tab (use for off-site links) */
  external?: boolean;
};

export default function SlidingFillList({ items, className = "" }: { items: SlidingFillItem[]; className?: string }) {
  return (
    <ul className={`sfl ${className}`.trim()}>
      {items.map((item, i) => {
        const inner = (
          <>
            <span className="sfl-fill" aria-hidden="true" />
            <span className="sfl-label">{item.label}</span>
            <span className="sfl-icon" aria-hidden="true">
              <svg width="12" height="12" viewBox="0 0 8 8" fill="none">
                <path d="M1 7.5L7.5 1M7.5 1V6.5M7.5 1H1.5" stroke="currentColor" />
              </svg>
            </span>
          </>
        );
        return (
          <li key={`${item.href}-${i}`}>
            {item.external ? (
              <a className="sfl-row" href={item.href} target="_blank" rel="noopener noreferrer">
                {inner}
              </a>
            ) : (
              <Link className="sfl-row" href={item.href}>
                {inner}
              </Link>
            )}
          </li>
        );
      })}
    </ul>
  );
}
