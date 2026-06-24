import { Check, Copy } from "lucide-react";
import { useState } from "react";
import type { CompilationResult } from "../../../types/runtime";

interface RawJsonTabProps {
  result: CompilationResult;
}

export function RawJsonTab({ result }: RawJsonTabProps) {
  const [copied, setCopied] = useState(false);
  const json = JSON.stringify(result, null, 2);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(json);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div style={{ position: "relative" }}>
      <button
        type="button"
        className="copy-button"
        onClick={handleCopy}
        style={{
          position: "absolute",
          top: "var(--space-3)",
          right: "var(--space-3)",
          display: "inline-flex",
          alignItems: "center",
          gap: "var(--space-1)",
          padding: "4px 10px",
          borderRadius: "var(--radius-sm)",
          border: "1px solid var(--color-border)",
          background: "var(--color-surface-2)",
          color: "var(--color-text-secondary)",
          fontSize: 12,
          fontWeight: 600,
          cursor: "pointer",
          transition: "border-color 0.15s ease, color 0.15s ease",
        }}
      >
        {copied ? <Check size={13} /> : <Copy size={13} />}
        {copied ? "Copied" : "Copy"}
      </button>
      <pre
        style={{
          margin: 0,
          padding: "var(--space-4)",
          borderRadius: "var(--radius-md)",
          border: "1px solid var(--color-border)",
          background: "var(--color-surface-1)",
          color: "var(--color-text-primary)",
          fontFamily: "var(--font-mono)",
          fontSize: 12,
          lineHeight: 1.6,
          overflow: "auto",
          maxHeight: 640,
        }}
      >
        {json}
      </pre>
    </div>
  );
}
