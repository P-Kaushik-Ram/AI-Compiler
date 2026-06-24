import { HeartPulse, Layers, PenLine, Users, type LucideIcon } from "lucide-react";
import type { BenchmarkPreset } from "../../store/evaluationStore";

interface PresetOption {
  id: BenchmarkPreset;
  label: string;
  description: string;
  icon: LucideIcon;
}

const OPTIONS: PresetOption[] = [
  { id: "crm", label: "CRM Benchmark", description: "4 CRM prompts.", icon: Users },
  { id: "mixed", label: "Mixed Domains", description: "5 cross-domain prompts.", icon: Layers },
  { id: "healthcare", label: "Healthcare Benchmark", description: "4 healthcare prompts.", icon: HeartPulse },
  { id: "custom", label: "Custom Dataset", description: "Enter your own prompts.", icon: PenLine },
];

interface PresetSelectorProps {
  value: BenchmarkPreset;
  onChange: (preset: BenchmarkPreset) => void;
  disabled?: boolean;
}

export function PresetSelector({ value, onChange, disabled }: PresetSelectorProps) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
        gap: "var(--space-3)",
      }}
    >
      {OPTIONS.map((option) => {
        const Icon = option.icon;
        const isActive = value === option.id;
        return (
          <button
            key={option.id}
            type="button"
            className="prompt-card"
            aria-pressed={isActive}
            disabled={disabled}
            onClick={() => onChange(option.id)}
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "flex-start",
              gap: "var(--space-2)",
              textAlign: "left",
              padding: "var(--space-4)",
              borderRadius: "var(--radius-md)",
              border: `1px solid ${isActive ? "var(--color-brand)" : "var(--color-border)"}`,
              background: isActive ? "var(--color-brand-muted)" : "var(--color-surface-1)",
              color: "inherit",
              cursor: disabled ? "default" : "pointer",
              opacity: disabled ? 0.5 : 1,
              transition: "border-color 0.15s ease, background 0.15s ease",
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
                background: isActive ? "var(--color-brand)" : "var(--color-brand-muted)",
              }}
            >
              <Icon size={18} color={isActive ? "#fff" : "var(--color-brand)"} />
            </div>
            <span style={{ fontSize: 13, fontWeight: 600, color: "var(--color-text-primary)" }}>{option.label}</span>
            <span style={{ fontSize: 12, color: "var(--color-text-secondary)", lineHeight: 1.4 }}>
              {option.description}
            </span>
          </button>
        );
      })}
    </div>
  );
}
