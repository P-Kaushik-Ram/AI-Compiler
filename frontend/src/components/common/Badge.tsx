import type { ReactNode } from "react";

export type BadgeVariant = "neutral" | "brand" | "success" | "warning" | "error" | "info";

interface BadgeProps {
  children: ReactNode;
  variant?: BadgeVariant;
}

const VARIANT_STYLES: Record<BadgeVariant, { bg: string; fg: string }> = {
  neutral: { bg: "var(--color-neutral-muted)", fg: "var(--color-text-secondary)" },
  brand: { bg: "var(--color-brand-muted)", fg: "var(--color-brand)" },
  success: { bg: "var(--color-success-muted)", fg: "var(--color-success)" },
  warning: { bg: "var(--color-warning-muted)", fg: "var(--color-warning)" },
  error: { bg: "var(--color-error-muted)", fg: "var(--color-error)" },
  info: { bg: "var(--color-info-muted)", fg: "var(--color-info)" },
};

export function Badge({ children, variant = "neutral" }: BadgeProps) {
  const { bg, fg } = VARIANT_STYLES[variant];
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "var(--space-1)",
        padding: "2px 8px",
        borderRadius: "var(--radius-sm)",
        background: bg,
        color: fg,
        fontSize: 12,
        fontWeight: 600,
        fontFamily: "var(--font-mono)",
        whiteSpace: "nowrap",
      }}
    >
      {children}
    </span>
  );
}
