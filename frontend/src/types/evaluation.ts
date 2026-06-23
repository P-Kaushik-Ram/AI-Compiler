/** Mirrors backend/app/models/evaluation.py (request/response shapes used by the frontend) */

export interface CaseExpectation {
  expected_overall_status: string | null;
  expected_domain: string | null;
  expected_min_confidence: number | null;
  expect_halt: boolean;
}

export interface DatasetCase {
  case_id: string;
  prompt: string;
  category: string | null;
  expectation: CaseExpectation | null;
}

export interface DatasetError {
  case_id: string | null;
  raw_line_number: number | null;
  error: string;
}

export type FailureCategory =
  | "intent_ambiguous"
  | "design_inconsistent"
  | "schema_inconsistent"
  | "validation_failed"
  | "infrastructure_error";

export type BenchmarkStatus = "complete" | "failed_to_load";

export interface Distribution {
  count: number;
  mean: number;
  min: number;
  max: number;
  p50_approx: number;
  p95_approx: number;
}

export interface BenchmarkResult {
  benchmark_id: string;
  version: string;
  dataset_name: string;
  dataset_size: number;
  compiler_version: string;
  started_at: string;
  completed_at: string;
  total_duration_ms: number;
  success_rate: number;
  halt_rate: number;
  error_rate: number;
  validation_pass_rate: number;
  confidence_by_stage: Record<string, Distribution>;
  duration_by_stage_ms: Record<string, Distribution>;
  failure_category_counts: Record<string, number>;
  validation_finding_severity_counts: Record<string, number>;
  dataset_categories: Record<string, number>;
  dataset_errors: DatasetError[];
  status: BenchmarkStatus;
}
