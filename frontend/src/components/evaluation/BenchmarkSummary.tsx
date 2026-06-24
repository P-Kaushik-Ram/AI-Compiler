import { CheckCircle2, Clock, OctagonAlert, ShieldCheck, XCircle, type LucideIcon } from "lucide-react";
import type { BenchmarkResult } from "../../types/evaluation";
import { Badge } from "../common/Badge";
import { StatusPill } from "../common/StatusPill";
import type { StatusKind } from "../common/StatusPill";
import { KIND_TEXT_COLOR, formatConfidence as formatPercent, formatDuration, statusToKind } from "../../lib/status";

interface BenchmarkSummaryProps {
  result: BenchmarkResult;
}

export function BenchmarkSummary({ result }: BenchmarkSummaryProps) {
  return (
    <div style={{ marginBottom: "var(--space-6)" }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "var(--space-3)",
          marginBottom: "var(--space-4)",
          flexWrap: "wrap",
        }}
      >
        <strong style={{ fontSize: 14 }}>{result.dataset_name}</strong>
        <StatusPill label={result.status} status={statusToKind(result.status)} />
        <Badge variant="neutral">compiler {result.compiler_version}</Badge>
        <Badge variant="neutral">
          {result.dataset_size} case{result.dataset_size === 1 ? "" : "s"}
        </Badge>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
          gap: "var(--space-4)",
        }}
      >
        <MetricCard icon={CheckCircle2} label="Success Rate" value={formatPercent(result.success_rate)} kind="success" />
        <MetricCard
          icon={OctagonAlert}
          label="Halt Rate"
          value={formatPercent(result.halt_rate)}
          kind={result.halt_rate > 0 ? "warning" : "neutral"}
        />
        <MetricCard
          icon={XCircle}
          label="Error Rate"
          value={formatPercent(result.error_rate)}
          kind={result.error_rate > 0 ? "error" : "neutral"}
        />
        <MetricCard icon={ShieldCheck} label="Validation Pass Rate" value={formatPercent(result.validation_pass_rate)} />
        <MetricCard icon={Clock} label="Total Duration" value={formatDuration(result.total_duration_ms)} />
      </div>
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
      <div
        style={{
          marginTop: "var(--space-2)",
          fontSize: 20,
          fontWeight: 700,
          color: kind ? KIND_TEXT_COLOR[kind] : "var(--color-text-primary)",
        }}
      >
        {value}
      </div>
    </div>
  );
}
