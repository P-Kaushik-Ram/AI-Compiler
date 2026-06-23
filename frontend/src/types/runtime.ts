/** Mirrors backend/app/models/runtime.py */
import type { DataSchema } from "./dataSchema";
import type { IntentIR } from "./intent";
import type { SystemDesign } from "./systemDesign";
import type { ValidationReport } from "./validation";

export type StageName = "intent_extraction" | "system_design" | "schema_generation" | "validation";
export type OverallStatus = "succeeded" | "succeeded_with_warnings" | "halted" | "errored";
export type FinalDecision = "proceed" | "proceed_with_warnings" | "halt" | "not_reached";

export interface StageSummary {
  stage_name: StageName;
  status: string;
  duration_ms: number;
  confidence: number | null;
  summary: string;
}

export interface CompilationResult {
  compilation_id: string;
  version: string;
  started_at: string;
  completed_at: string;
  total_duration_ms: number;
  overall_status: OverallStatus;
  final_decision: FinalDecision;
  stage_summaries: StageSummary[];
  intent_ir: IntentIR | null;
  system_design: SystemDesign | null;
  data_schema: DataSchema | null;
  validation_report: ValidationReport | null;
  error: string | null;
}
