import { AlertTriangle } from "lucide-react";

interface ErrorBannerProps {
  message: string;
  detail?: string;
  onRetry?: () => void;
}

export function ErrorBanner({ message, detail, onRetry }: ErrorBannerProps) {
  return (
    <div
      role="alert"
      style={{
        display: "flex",
        alignItems: "flex-start",
        gap: "var(--space-3)",
        padding: "var(--space-3) var(--space-4)",
        borderRadius: "var(--radius-md)",
        background: "var(--color-error-muted)",
        border: "1px solid var(--color-error)",
        color: "var(--color-text-primary)",
      }}
    >
      <AlertTriangle size={18} color="var(--color-error)" style={{ flexShrink: 0, marginTop: 2 }} />
      <div style={{ flex: 1 }}>
        <p style={{ margin: 0, fontSize: 13, fontWeight: 600 }}>{message}</p>
        {detail && (
          <p style={{ margin: "4px 0 0", fontSize: 12, color: "var(--color-text-secondary)" }}>
            {detail}
          </p>
        )}
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            flexShrink: 0,
            padding: "4px 10px",
            borderRadius: "var(--radius-sm)",
            border: "1px solid var(--color-error)",
            background: "transparent",
            color: "var(--color-error)",
            fontSize: 12,
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          Retry
        </button>
      )}
    </div>
  );
}
