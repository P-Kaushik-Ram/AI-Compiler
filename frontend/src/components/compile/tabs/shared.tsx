import type { ReactNode } from "react";

interface TabSectionProps {
  title: string;
  count?: number;
  children: ReactNode;
}

/** A titled block grouping one category of artifact data within a result tab. */
export function TabSection({ title, count, children }: TabSectionProps) {
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

interface ListSectionProps<T> {
  title: string;
  items: T[];
  renderItem: (item: T, index: number) => ReactNode;
  emptyLabel?: string;
}

/** A TabSection whose body is either an empty-state line or a vertical stack of TabRows. */
export function ListSection<T>({ title, items, renderItem, emptyLabel = "None detected." }: ListSectionProps<T>) {
  return (
    <TabSection title={title} count={items.length}>
      {items.length === 0 ? (
        <Muted>{emptyLabel}</Muted>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
          {items.map(renderItem)}
        </div>
      )}
    </TabSection>
  );
}

/** A single bordered row used for every item rendered inside a ListSection. */
export function TabRow({ children }: { children: ReactNode }) {
  return (
    <div
      style={{
        padding: "var(--space-3) var(--space-4)",
        borderRadius: "var(--radius-md)",
        border: "1px solid var(--color-border)",
        background: "var(--color-surface-1)",
        fontSize: 12,
      }}
    >
      {children}
    </div>
  );
}

export function Muted({ children }: { children: ReactNode }) {
  return <p style={{ margin: 0, fontSize: 12, color: "var(--color-text-secondary)" }}>{children}</p>;
}
