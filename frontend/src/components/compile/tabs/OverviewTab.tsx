import { AlertTriangle, CheckCircle2, Clock, Gauge, MinusCircle, XCircle, type LucideIcon } from "lucide-react";
import type { CompilationResult, FinalDecision } from "../../../types/runtime";
import { ErrorBanner } from "../../common/ErrorBanner";
import { StatusPill } from "../../common/StatusPill";
import type { StatusKind } from "../../common/StatusPill";
import { formatConfidence, formatDuration, formatLabel, statusToKind } from "../../../lib/status";
import { TabSection } from "./shared";

const DECISION_LABEL: Record<FinalDecision, string> = {
  proceed: "Proceed",
  proceed_with_warnings: "Proceed with Warnings",
  halt: "Halt",
  not_reached: "Not Reached",
};

const DECISION_ICON: Record<FinalDecision, LucideIcon> = {
  proceed: CheckCircle2,
  proceed_with_warnings: AlertTriangle,
  halt: XCircle,
  not_reached: MinusCircle,
};

const KIND_COLOR: Record<StatusKind, string> = {
  neutral: "var(--color-text-primary)",
  success: "var(--color-success)",
  warning: "var(--color-warning)",
  error: "var(--color-error)",
  info: "var(--color-info)",
  pending: "var(--color-text-secondary)",
};

interface OverviewTabProps {
  result: CompilationResult;
}

export function OverviewTab({ result }: OverviewTabProps) {
  const overallConfidence = result.validation_report?.confidence ?? null;
  const decisionKind = statusToKind(result.final_decision);

  return (
    <div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "var(--space-4)",
          marginBottom: "var(--space-6)",
        }}
      >
        <MetricCard
          icon={DECISION_ICON[result.final_decision]}
          label="Compilation Decision"
          value={DECISION_LABEL[result.final_decision]}
          kind={decisionKind}
        />
        <MetricCard icon={Clock} label="Total Duration" value={formatDuration(result.total_duration_ms)} />
        <MetricCard icon={Gauge} label="Overall Confidence" value={formatConfidence(overallConfidence)} />
      </div>

      {result.error && <ErrorBanner message="The compilation pipeline reported an error." detail={result.error} />}

      <TabSection title="Pipeline Summary" count={result.stage_summaries.length}>
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
          {result.stage_summaries.map((summary) => (
            <div
              key={summary.stage_name}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "var(--space-3)",
                padding: "var(--space-3) var(--space-4)",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--color-border)",
                background: "var(--color-surface-1)",
              }}
            >
              <span style={{ fontSize: 13, fontWeight: 600, minWidth: 150 }}>{formatLabel(summary.stage_name)}</span>
              <StatusPill label={summary.status} status={statusToKind(summary.status)} />
              <span style={{ flex: 1, fontSize: 12, color: "var(--color-text-secondary)" }}>{summary.summary}</span>
              <span style={{ fontSize: 12, fontFamily: "var(--font-mono)", color: "var(--color-text-secondary)" }}>
                {formatDuration(summary.duration_ms)}
              </span>
            </div>
          ))}
        </div>
      </TabSection>
    </div>
  );
}

interface MetricCardProps {
  icon: LucideIcon;
  label: string;
  value: string;
  kind?: StatusKind;
}

function MetricCard({ icon: Icon, label, value, kind }: MetricCardProps) {
  return (
    <div
      style={{
        padding: "var(--space-4)",
        borderRadius: "var(--radius-md)",
        border: "1px solid var(--color-border)",
        background: "var(--color-surface-1)",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "var(--space-2)",
          color: "var(--color-text-secondary)",
          fontSize: 11,
          fontWeight: 700,
          textTransform: "uppercase",
          letterSpacing: "0.04em",
        }}
      >
        <Icon size={14} />
        {label}
      </div>
      <div style={{ marginTop: "var(--space-2)", fontSize: 20, fontWeight: 700, color: kind ? KIND_COLOR[kind] : "var(--color-text-primary)" }}>
        {value}
      </div>
    </div>
  );
}
