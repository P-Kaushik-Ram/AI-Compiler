import type { BenchmarkResult } from "../../../frontend/src/types/evaluation";

/** A minimal but fully-typed BenchmarkResult used across evaluation-feature tests. */
export const MOCK_BENCHMARK_RESULT: BenchmarkResult = {
  benchmark_id: "22222222-2222-2222-2222-222222222222",
  version: "1.0",
  dataset_name: "crm-preset",
  dataset_size: 4,
  compiler_version: "1.0",
  started_at: "2026-01-01T00:00:00Z",
  completed_at: "2026-01-01T00:00:05Z",
  total_duration_ms: 42.5,
  success_rate: 0.75,
  halt_rate: 0.25,
  error_rate: 0,
  validation_pass_rate: 0.5,
  confidence_by_stage: {
    intent_extraction: { count: 4, mean: 0.85, min: 0.1, max: 0.95, p50_approx: 0.9, p95_approx: 0.95 },
    system_design: { count: 4, mean: 0.8, min: 0.1, max: 0.9, p50_approx: 0.85, p95_approx: 0.9 },
    schema_generation: { count: 4, mean: 0.8, min: 0.1, max: 0.9, p50_approx: 0.85, p95_approx: 0.9 },
    validation: { count: 4, mean: 0.75, min: 0.05, max: 0.9, p50_approx: 0.8, p95_approx: 0.9 },
  },
  duration_by_stage_ms: {
    intent_extraction: { count: 4, mean: 1.2, min: 0.8, max: 1.8, p50_approx: 1.1, p95_approx: 1.8 },
    system_design: { count: 4, mean: 2.1, min: 1.5, max: 2.9, p50_approx: 2.0, p95_approx: 2.9 },
    schema_generation: { count: 4, mean: 1.8, min: 1.2, max: 2.4, p50_approx: 1.7, p95_approx: 2.4 },
    validation: { count: 4, mean: 0.9, min: 0.5, max: 1.3, p50_approx: 0.9, p95_approx: 1.3 },
  },
  failure_category_counts: {
    intent_ambiguous: 1,
    design_inconsistent: 0,
    schema_inconsistent: 0,
    validation_failed: 0,
    infrastructure_error: 0,
  },
  validation_finding_severity_counts: {
    info: 0,
    warning: 0,
    error: 0,
    critical: 3,
  },
  dataset_categories: {
    crm: 4,
  },
  dataset_errors: [],
  status: "complete",
};
