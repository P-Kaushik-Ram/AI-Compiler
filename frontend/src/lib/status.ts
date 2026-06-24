/** Maps raw backend status/severity strings to the presentational kinds the UI renders.
 *
 * This is purely a display mapping — it never recomputes a decision the compiler already
 * made (e.g. pipeline_decision, status, confidence). Every value consumed here comes directly
 * off a CompilationResult produced by RuntimeService.
 */
import type { BadgeVariant } from "../components/common/Badge";
import type { StatusKind } from "../components/common/StatusPill";

const SUCCESS_STATUSES = new Set(["complete", "passed", "succeeded", "proceed"]);
const WARNING_STATUSES = new Set([
  "needs_clarification",
  "passed_with_warnings",
  "succeeded_with_warnings",
  "proceed_with_warnings",
]);
const ERROR_STATUSES = new Set(["rejected", "failed", "error", "halted", "halt", "errored"]);
const NEUTRAL_STATUSES = new Set(["skipped", "not_reached"]);

export function statusToKind(status: string | null | undefined): StatusKind {
  if (!status) return "pending";
  if (SUCCESS_STATUSES.has(status)) return "success";
  if (WARNING_STATUSES.has(status)) return "warning";
  if (ERROR_STATUSES.has(status)) return "error";
  if (NEUTRAL_STATUSES.has(status)) return "neutral";
  return "neutral";
}

const SEVERITY_VARIANT: Record<string, BadgeVariant> = {
  info: "neutral",
  low: "neutral",
  advisory: "warning",
  medium: "warning",
  warning: "warning",
  high: "error",
  error: "error",
  blocking: "error",
  critical: "error",
};

export function severityToVariant(severity: string): BadgeVariant {
  return SEVERITY_VARIANT[severity] ?? "neutral";
}

export function formatConfidence(confidence: number | null | undefined): string {
  if (confidence === null || confidence === undefined) return "—";
  return `${Math.round(confidence * 100)}%`;
}

export function formatDuration(durationMs: number | null | undefined): string {
  if (durationMs === null || durationMs === undefined) return "—";
  if (durationMs < 1000) return `${durationMs.toFixed(1)} ms`;
  return `${(durationMs / 1000).toFixed(2)} s`;
}

export function formatLabel(value: string): string {
  return value.replace(/_/g, " ");
}
