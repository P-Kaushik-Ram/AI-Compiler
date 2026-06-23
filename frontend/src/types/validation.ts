/** Mirrors backend/app/models/validation.py */

export type ValidationCategory =
  | "missing_entity"
  | "orphan_relationship"
  | "invalid_reference"
  | "duplicate_definition"
  | "naming_conflict"
  | "risk_propagation_failure"
  | "missing_required_field"
  | "broken_traceability"
  | "cross_stage_inconsistency";

export type FindingSeverity = "info" | "warning" | "error" | "critical";
export type ValidationStage = "intent" | "system_design" | "data_schema" | "cross_stage";
export type PipelineDecision = "proceed" | "proceed_with_warnings" | "halt";
export type ValidationStatus = "passed" | "passed_with_warnings" | "failed";

export interface ValidationFinding {
  finding_id: string;
  category: ValidationCategory;
  severity: FindingSeverity;
  stage: ValidationStage;
  message: string;
  related_field: string | null;
  recommendation: string;
}

export interface ConsistencySummary {
  entities_checked: number;
  relationships_checked: number;
  modules_checked: number;
  schema_entities_checked: number;
  upstream_ambiguities_carried: number;
  acknowledged_gaps: number;
}

export interface ValidationReport {
  validation_id: string;
  version: string;
  source_intent_id: string;
  source_design_id: string;
  source_schema_id: string;
  findings: ValidationFinding[];
  consistency_summary: ConsistencySummary;
  confidence: number;
  pipeline_decision: PipelineDecision;
  status: ValidationStatus;
}
