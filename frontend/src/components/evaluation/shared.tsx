import type { ReactNode } from "react";

interface SectionProps {
  title: string;
  count?: number;
  children: ReactNode;
}

/** A titled block grouping one category of benchmark data. */
export function Section({ title, count, children }: SectionProps) {
  return (
    <section style={{ marginBottom: "var(--space-6)" }}>
      <h3
        style={{
          margin: "0 0 var(--space-3)",
          fontSize: 12,
          fontWeight: 700,
          color: "var(--color-text-secondary)",
          textTransform: "uppercase",
          letterSpacing: "0.04em",
        }}
      >
        {title}
        {count !== undefined && (
          <span style={{ marginLeft: "var(--space-2)", fontWeight: 400 }}>({count})</span>
        )}
      </h3>
      {children}
    </section>
  );
}

export function Muted({ children }: { children: ReactNode }) {
  return <p style={{ margin: 0, fontSize: 12, color: "var(--color-text-secondary)" }}>{children}</p>;
}
