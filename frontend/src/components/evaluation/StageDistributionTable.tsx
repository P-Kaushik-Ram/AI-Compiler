import type { CSSProperties } from "react";
import type { BenchmarkResult, Distribution } from "../../types/evaluation";
import { formatConfidence, formatDuration, formatLabel } from "../../lib/status";
import { Muted, Section } from "./shared";

const STAGE_ORDER = ["intent_extraction", "system_design", "schema_generation", "validation"];
const TABLE_HEADINGS = ["Stage", "Count", "Mean", "Min", "Max", "P50", "P95"];

const TH_STYLE: CSSProperties = {
  textAlign: "left",
  padding: "var(--space-2) var(--space-3)",
  borderBottom: "1px solid var(--color-border)",
  color: "var(--color-text-secondary)",
  fontWeight: 600,
  textTransform: "uppercase",
  fontSize: 11,
  letterSpacing: "0.04em",
};

const TD_STYLE: CSSProperties = {
  padding: "var(--space-2) var(--space-3)",
  borderBottom: "1px solid var(--color-border)",
  fontFamily: "var(--font-mono)",
};

interface StageDistributionTableProps {
  result: BenchmarkResult;
}

/** Renders confidence_by_stage and duration_by_stage_ms exactly as returned by the
 * StreamingAggregator — every value here is formatted, never recomputed. */
export function StageDistributionTable({ result }: StageDistributionTableProps) {
  return (
    <Section title="Stage Metrics">
      <DistributionTable caption="Confidence by Stage" data={result.confidence_by_stage} formatValue={formatConfidence} />
      <div style={{ height: "var(--space-4)" }} />
      <DistributionTable caption="Duration by Stage" data={result.duration_by_stage_ms} formatValue={formatDuration} />
    </Section>
  );
}

interface DistributionTableProps {
  caption: string;
  data: Record<string, Distribution>;
  formatValue: (value: number) => string;
}

function DistributionTable({ caption, data, formatValue }: DistributionTableProps) {
  const stages = STAGE_ORDER.filter((stage) => data[stage] !== undefined);

  return (
    <div>
      <p style={{ fontSize: 12, fontWeight: 600, margin: "0 0 var(--space-2)" }}>{caption}</p>
      {stages.length === 0 ? (
        <Muted>No data recorded.</Muted>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
          <thead>
            <tr>
              {TABLE_HEADINGS.map((heading) => (
                <th key={heading} style={TH_STYLE}>
                  {heading}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {stages.map((stage) => {
              const distribution = data[stage];
              return (
                <tr key={stage}>
                  <td style={TD_STYLE}>{formatLabel(stage)}</td>
                  <td style={TD_STYLE}>{distribution.count}</td>
                  <td style={TD_STYLE}>{formatValue(distribution.mean)}</td>
                  <td style={TD_STYLE}>{formatValue(distribution.min)}</td>
                  <td style={TD_STYLE}>{formatValue(distribution.max)}</td>
                  <td style={TD_STYLE}>{formatValue(distribution.p50_approx)}</td>
                  <td style={TD_STYLE}>{formatValue(distribution.p95_approx)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}
