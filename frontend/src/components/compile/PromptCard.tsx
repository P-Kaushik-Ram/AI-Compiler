import type { LucideIcon } from "lucide-react";

interface PromptCardProps {
  icon: LucideIcon;
  title: string;
  description: string;
  onClick: () => void;
  disabled?: boolean;
}

export function PromptCard({ icon: Icon, title, description, onClick, disabled }: PromptCardProps) {
  return (
    <button
      type="button"
      className="prompt-card"
      onClick={onClick}
      disabled={disabled}
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "flex-start",
        gap: "var(--space-2)",
        textAlign: "left",
        padding: "var(--space-4)",
        borderRadius: "var(--radius-md)",
        border: "1px solid var(--color-border)",
        background: "var(--color-surface-1)",
        color: "inherit",
        cursor: disabled ? "default" : "pointer",
        opacity: disabled ? 0.5 : 1,
        transition: "border-color 0.15s ease, transform 0.15s ease",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          width: 36,
          height: 36,
          borderRadius: "var(--radius-sm)",
          background: "var(--color-brand-muted)",
        }}
      >
        <Icon size={18} color="var(--color-brand)" />
      </div>
      <span style={{ fontSize: 13, fontWeight: 600, color: "var(--color-text-primary)" }}>{title}</span>
      <span style={{ fontSize: 12, color: "var(--color-text-secondary)", lineHeight: 1.4 }}>
        {description}
      </span>
    </button>
  );
}
