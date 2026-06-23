export type StatusKind = "neutral" | "success" | "warning" | "error" | "info" | "pending";

interface StatusPillProps {
  label: string;
  status?: StatusKind;
}

const DOT_COLOR: Record<StatusKind, string> = {
  neutral: "var(--color-text-secondary)",
  success: "var(--color-success)",
  warning: "var(--color-warning)",
  error: "var(--color-error)",
  info: "var(--color-info)",
  pending: "var(--color-text-secondary)",
};

/** A label with a colored status dot — used for the top-nav test badge and, later, pipeline stage states. */
export function StatusPill({ label, status = "neutral" }: StatusPillProps) {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "var(--space-2)",
        padding: "2px 8px",
        borderRadius: "var(--radius-sm)",
        background: "var(--color-surface-2)",
        border: "1px solid var(--color-border)",
        fontSize: 12,
        fontWeight: 500,
        color: "var(--color-text-secondary)",
        whiteSpace: "nowrap",
      }}
    >
      <span
        aria-hidden="true"
        style={{
          width: 6,
          height: 6,
          borderRadius: "50%",
          background: DOT_COLOR[status],
          flexShrink: 0,
        }}
      />
      {label}
    </span>
  );
}
