import { ShieldCheck } from "lucide-react";
import type { ValidationReport } from "../../../types/validation";
import { Badge } from "../../common/Badge";
import { EmptyState } from "../../common/EmptyState";
import { StatusPill } from "../../common/StatusPill";
import { formatConfidence, formatLabel, severityToVariant, statusToKind } from "../../../lib/status";
import { ListSection, TabRow, TabSection } from "./shared";

interface ValidationTabProps {
  validationReport: ValidationReport | null;
}

export function ValidationTab({ validationReport }: ValidationTabProps) {
  if (!validationReport) {
    return (
      <EmptyState
        icon={ShieldCheck}
        title="Validation stage not reached"
        description="This compilation did not produce a ValidationReport."
      />
    );
  }

  const decisionKind = statusToKind(validationReport.pipeline_decision);
  const decisionVariant = decisionKind === "success" ? "success" : decisionKind === "warning" ? "warning" : "error";

  const summary = validationReport.consistency_summary;
  const summaryEntries: Array<[string, number]> = [
    ["Entities Checked", summary.entities_checked],
    ["Relationships Checked", summary.relationships_checked],
    ["Modules Checked", summary.modules_checked],
    ["Schema Entities Checked", summary.schema_entities_checked],
    ["Upstream Ambiguities Carried", summary.upstream_ambiguities_carried],
    ["Acknowledged Gaps", summary.acknowledged_gaps],
  ];

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)", marginBottom: "var(--space-6)", flexWrap: "wrap" }}>
        <Badge variant={decisionVariant}>{formatLabel(validationReport.pipeline_decision)}</Badge>
        <StatusPill label={validationReport.status} status={statusToKind(validationReport.status)} />
        <span style={{ fontSize: 12, color: "var(--color-text-secondary)", fontFamily: "var(--font-mono)" }}>
          {formatConfidence(validationReport.confidence)} confidence
        </span>
      </div>

      <TabSection title="Consistency Summary">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: "var(--space-3)" }}>
          {summaryEntries.map(([label, value]) => (
            <div
              key={label}
              style={{
                padding: "var(--space-3) var(--space-4)",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--color-border)",
                background: "var(--color-surface-1)",
              }}
            >
              <div style={{ fontSize: 11, color: "var(--color-text-secondary)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                {label}
              </div>
              <div style={{ fontSize: 18, fontWeight: 700, marginTop: 2 }}>{value}</div>
            </div>
          ))}
        </div>
      </TabSection>

      <ListSection
        title="Findings"
        items={validationReport.findings}
        emptyLabel="No findings — every stage is consistent."
        renderItem={(finding) => (
          <TabRow key={finding.finding_id}>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap" }}>
              <Badge variant={severityToVariant(finding.severity)}>{finding.severity}</Badge>
              <Badge variant="neutral">{formatLabel(finding.category)}</Badge>
              <Badge variant="neutral">{formatLabel(finding.stage)}</Badge>
            </div>
            <p style={{ margin: "4px 0 0" }}>{finding.message}</p>
            <p style={{ margin: "4px 0 0", color: "var(--color-text-secondary)", fontStyle: "italic" }}>
              {finding.recommendation}
            </p>
          </TabRow>
        )}
      />
    </div>
  );
}
