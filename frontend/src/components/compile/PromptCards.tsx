import { PROMPT_EXAMPLES } from "../../lib/promptExamples";
import { PromptCard } from "./PromptCard";

interface PromptCardsProps {
  onSelect: (prompt: string) => void;
  disabled?: boolean;
}

export function PromptCards({ onSelect, disabled }: PromptCardsProps) {
  return (
    <div>
      <p
        style={{
          margin: "0 0 var(--space-3)",
          fontSize: 12,
          fontWeight: 600,
          color: "var(--color-text-secondary)",
          textTransform: "uppercase",
          letterSpacing: "0.04em",
        }}
      >
        Or start from an example
      </p>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "var(--space-3)",
        }}
      >
        {PROMPT_EXAMPLES.map((example) => (
          <PromptCard
            key={example.id}
            icon={example.icon}
            title={example.title}
            description={example.description}
            disabled={disabled}
            onClick={() => onSelect(example.prompt)}
          />
        ))}
      </div>
    </div>
  );
}
