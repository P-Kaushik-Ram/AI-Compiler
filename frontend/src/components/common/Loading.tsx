import { Loader2 } from "lucide-react";

interface LoadingProps {
  label?: string;
  size?: "sm" | "md" | "lg";
}

const ICON_SIZE: Record<NonNullable<LoadingProps["size"]>, number> = {
  sm: 14,
  md: 20,
  lg: 28,
};

export function Loading({ label, size = "md" }: LoadingProps) {
  return (
    <div style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-2)" }}>
      <Loader2 className="spin" size={ICON_SIZE[size]} color="var(--color-brand)" />
      {label && <span style={{ fontSize: 13, color: "var(--color-text-secondary)" }}>{label}</span>}
    </div>
  );
}
