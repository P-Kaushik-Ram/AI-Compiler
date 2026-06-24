interface CustomDatasetEditorProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export function CustomDatasetEditor({ value, onChange, disabled }: CustomDatasetEditorProps) {
  const caseCount = value
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0).length;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
      <label
        htmlFor="custom-dataset-input"
        style={{ fontSize: 12, fontWeight: 600, color: "var(--color-text-secondary)" }}
      >
        Enter one prompt per line
      </label>
      <textarea
        id="custom-dataset-input"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        disabled={disabled}
        rows={6}
        placeholder={
          "Build a CRM where users can manage contacts.\nBuild a todo app with due dates.\n..."
        }
        style={{
          width: "100%",
          resize: "vertical",
          padding: "var(--space-4)",
          borderRadius: "var(--radius-md)",
          border: "1px solid var(--color-border)",
          background: "var(--color-surface-1)",
          color: "var(--color-text-primary)",
          fontFamily: "var(--font-ui)",
          fontSize: 14,
          lineHeight: 1.6,
          outline: "none",
        }}
      />
      <span style={{ fontSize: 12, color: "var(--color-text-secondary)", fontFamily: "var(--font-mono)" }}>
        {caseCount} {caseCount === 1 ? "case" : "cases"}
      </span>
    </div>
  );
}
