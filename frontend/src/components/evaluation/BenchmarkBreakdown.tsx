import type { ReactNode } from "react";
import type { BenchmarkResult } from "../../types/evaluation";
import { Badge } from "../common/Badge";
import { formatLabel, severityToVariant } from "../../lib/status";
import { Muted, Section } from "./shared";

interface BenchmarkBreakdownProps {
  result: BenchmarkResult;
}

export function BenchmarkBreakdown({ result }: BenchmarkBreakdownProps) {
  const categoryEntries = Object.entries(result.dataset_categories);
  const failureEntries = Object.entries(result.failure_category_counts).filter(([, count]) => count > 0);
  const severityEntries = Object.entries(result.validation_finding_severity_counts).filter(
    ([, count]) => count > 0
  );

  return (
    <div>
      <Section title="Dataset Categories">
        {categoryEntries.length === 0 ? (
          <Muted>No categories recorded.</Muted>
        ) : (
          <BadgeRow>
            {categoryEntries.map(([category, count]) => (
              <Badge key={category} variant="neutral">
                {formatLabel(category)}: {count}
              </Badge>
            ))}
          </BadgeRow>
        )}
      </Section>

      <Section title="Failure Categories">
        {failureEntries.length === 0 ? (
          <Muted>No failures recorded.</Muted>
        ) : (
          <BadgeRow>
            {failureEntries.map(([category, count]) => (
              <Badge key={category} variant="error">
                {formatLabel(category)}: {count}
              </Badge>
            ))}
          </BadgeRow>
        )}
      </Section>

      <Section title="Validation Finding Severities">
        {severityEntries.length === 0 ? (
          <Muted>No validation findings recorded.</Muted>
        ) : (
          <BadgeRow>
            {severityEntries.map(([severity, count]) => (
              <Badge key={severity} variant={severityToVariant(severity)}>
                {severity}: {count}
              </Badge>
            ))}
          </BadgeRow>
        )}
      </Section>

      {result.dataset_errors.length > 0 && (
        <Section title="Dataset Errors" count={result.dataset_errors.length}>
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
            {result.dataset_errors.map((error, index) => (
              <div
                key={index}
                style={{
                  padding: "var(--space-3) var(--space-4)",
                  borderRadius: "var(--radius-md)",
                  border: "1px solid var(--color-error)",
                  background: "var(--color-error-muted)",
                  fontSize: 12,
                }}
              >
                {error.case_id && <strong>{error.case_id}: </strong>}
                {error.error}
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  );
}

function BadgeRow({ children }: { children: ReactNode }) {
  return <div style={{ display: "flex", flexWrap: "wrap", gap: "var(--space-2)" }}>{children}</div>;
}
