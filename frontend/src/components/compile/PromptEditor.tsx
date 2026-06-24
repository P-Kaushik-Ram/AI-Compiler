import { Loader2, Sparkles } from "lucide-react";
import type { KeyboardEvent } from "react";

const MAX_LENGTH = 4000;

interface PromptEditorProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  isLoading: boolean;
}

export function PromptEditor({ value, onChange, onSubmit, isLoading }: PromptEditorProps) {
  const isOverLimit = value.length > MAX_LENGTH;
  const canSubmit = value.trim().length > 0 && !isLoading && !isOverLimit;

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && (event.metaKey || event.ctrlKey) && canSubmit) {
      event.preventDefault();
      onSubmit();
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Describe the system you want to build... e.g. &quot;Build a CRM where users can sign up, log in, and manage contacts.&quot;"
        rows={6}
        disabled={isLoading}
        aria-label="System prompt"
        style={{
          width: "100%",
          resize: "vertical",
          padding: "var(--space-4)",
          borderRadius: "var(--radius-md)",
          border: `1px solid ${isOverLimit ? "var(--color-error)" : "var(--color-border)"}`,
          background: "var(--color-surface-1)",
          color: "var(--color-text-primary)",
          fontFamily: "var(--font-ui)",
          fontSize: 14,
          lineHeight: 1.6,
          outline: "none",
        }}
      />
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "var(--space-3)" }}>
        <span
          style={{
            fontSize: 12,
            fontFamily: "var(--font-mono)",
            color: isOverLimit ? "var(--color-error)" : "var(--color-text-secondary)",
          }}
        >
          {value.length.toLocaleString()} / {MAX_LENGTH.toLocaleString()} characters
        </span>
        <button
          type="button"
          className="compile-button"
          onClick={onSubmit}
          disabled={!canSubmit}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "var(--space-2)",
            padding: "10px 18px",
            borderRadius: "var(--radius-md)",
            border: "none",
            background: canSubmit ? "var(--color-brand)" : "var(--color-surface-2)",
            color: canSubmit ? "#fff" : "var(--color-text-secondary)",
            fontSize: 13,
            fontWeight: 600,
            cursor: canSubmit ? "pointer" : "not-allowed",
            transition: "filter 0.15s ease",
            flexShrink: 0,
          }}
        >
          {isLoading ? (
            <>
              <Loader2 className="spin" size={14} />
              Compiling…
            </>
          ) : (
            <>
              <Sparkles size={14} />
              Compile
            </>
          )}
        </button>
      </div>
    </div>
  );
}
