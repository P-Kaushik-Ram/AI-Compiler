import { ArrowDown, Brain, Database, Network, ShieldCheck, type LucideIcon } from "lucide-react";
import { useEffect, useState } from "react";
import type { StatusKind } from "../common/StatusPill";
import { StatusPill } from "../common/StatusPill";
import { Loading } from "../common/Loading";
import type { StageName, StageSummary } from "../../types/runtime";
import { formatConfidence, formatDuration, statusToKind } from "../../lib/status";

interface StageMeta {
  name: StageName;
  label: string;
  icon: LucideIcon;
}

const STAGES: StageMeta[] = [
  { name: "intent_extraction", label: "Intent Extraction", icon: Brain },
  { name: "system_design", label: "System Design", icon: Network },
  { name: "schema_generation", label: "Schema Generation", icon: Database },
  { name: "validation", label: "Validation", icon: ShieldCheck },
];

const ANIMATION_INTERVAL_MS = 700;

interface PipelineVisualizationProps {
  /** Stage summaries straight off a CompilationResult. Never recomputed — only formatted. */
  stageSummaries: StageSummary[];
  isCompiling: boolean;
}

export function PipelineVisualization({ stageSummaries, isCompiling }: PipelineVisualizationProps) {
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    if (!isCompiling) return;
    setActiveIndex(0);
    const interval = window.setInterval(() => {
      setActiveIndex((current) => (current + 1) % STAGES.length);
    }, ANIMATION_INTERVAL_MS);
    return () => window.clearInterval(interval);
  }, [isCompiling]);

  const summaryByStage = new Map(stageSummaries.map((summary) => [summary.stage_name, summary]));

  return (
    <div style={{ display: "flex", flexDirection: "column" }}>
      {STAGES.map((stage, index) => {
        const summary = summaryByStage.get(stage.name) ?? null;
        const isActive = isCompiling && index === activeIndex;
        return (
          <div key={stage.name} className="fade-in-up" style={{ animationDelay: `${index * 70}ms` }}>
            <StageRow stage={stage} summary={summary} isActive={isActive} isCompiling={isCompiling} />
            {index < STAGES.length - 1 && (
              <div style={{ display: "flex", justifyContent: "center", padding: "2px 0" }}>
                <ArrowDown
                  size={16}
                  color={isActive || summary ? "var(--color-brand)" : "var(--color-border)"}
                />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

interface StageRowProps {
  stage: StageMeta;
  summary: StageSummary | null;
  isActive: boolean;
  isCompiling: boolean;
}

function StageRow({ stage, summary, isActive, isCompiling }: StageRowProps) {
  const Icon = stage.icon;
  const kind: StatusKind = isActive ? "info" : summary ? statusToKind(summary.status) : "pending";
  const label = summary ? summary.status : isCompiling ? "pending" : "not reached";
  const description =
    summary?.summary ?? (isCompiling ? "Waiting for this stage to run." : "This stage was not reached.");

  return (
    <div
      className={isActive ? "pulse" : undefined}
      style={{
        display: "flex",
        alignItems: "center",
        gap: "var(--space-4)",
        padding: "var(--space-4)",
        borderRadius: "var(--radius-md)",
        border: `1px solid ${isActive ? "var(--color-brand)" : "var(--color-border)"}`,
        background: "var(--color-surface-1)",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          width: 40,
          height: 40,
          borderRadius: "var(--radius-sm)",
          background: "var(--color-brand-muted)",
          flexShrink: 0,
        }}
      >
        <Icon size={20} color="var(--color-brand)" />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap" }}>
          <span style={{ fontSize: 14, fontWeight: 600 }}>{stage.label}</span>
          {isActive ? <Loading size="sm" label="Running…" /> : <StatusPill label={label} status={kind} />}
        </div>
        <p style={{ margin: "4px 0 0", fontSize: 12, color: "var(--color-text-secondary)" }}>{description}</p>
      </div>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "flex-end",
          gap: 4,
          flexShrink: 0,
        }}
      >
        <span style={{ fontSize: 12, fontFamily: "var(--font-mono)", color: "var(--color-text-secondary)" }}>
          {formatConfidence(summary?.confidence)} confidence
        </span>
        <span style={{ fontSize: 12, fontFamily: "var(--font-mono)", color: "var(--color-text-secondary)" }}>
          {formatDuration(summary?.duration_ms)}
        </span>
      </div>
    </div>
  );
}
