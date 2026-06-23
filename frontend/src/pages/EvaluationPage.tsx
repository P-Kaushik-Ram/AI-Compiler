import { BarChart3 } from "lucide-react";
import { EmptyState } from "../components/common/EmptyState";

/** Placeholder for Phase 1. Benchmark presets and the metrics dashboard land in a later phase. */
export function EvaluationPage() {
  return (
    <EmptyState
      icon={BarChart3}
      title="Evaluation dashboard"
      description="Benchmark presets and run metrics arrive in a later phase."
    />
  );
}
