import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description?: string;
  action?: ReactNode;
}

export function EmptyState({ icon: Icon, title, description, action }: EmptyStateProps) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
        gap: "var(--space-3)",
        padding: "var(--space-6)",
        color: "var(--color-text-secondary)",
        height: "100%",
      }}
    >
      <Icon size={32} color="var(--color-brand)" />
      <h2 style={{ margin: 0, fontSize: 16, fontWeight: 600, color: "var(--color-text-primary)" }}>
        {title}
      </h2>
      {description && <p style={{ margin: 0, maxWidth: 360, fontSize: 13 }}>{description}</p>}
      {action}
    </div>
  );
}
