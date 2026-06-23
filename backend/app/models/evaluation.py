"""Pydantic models for the Evaluation Framework (batch execution, metrics, and reporting).

The Evaluation Framework is NOT a compiler stage: it has no IR of its own and never
participates in the compilation pipeline. These models describe its dataset input format
and its two output artifacts: ``EvaluationReport`` (one per dataset case, emitted immediately
after that case's compilation) and ``BenchmarkResult`` (one O(1)-sized aggregate per dataset
run, computed incrementally by a ``StreamingAggregator`` and never holding per-case detail).
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

FailureCategory = Literal[
    "intent_ambiguous",
    "design_inconsistent",
    "schema_inconsistent",
    "validation_failed",
    "infrastructure_error",
]
BenchmarkStatus = Literal["complete", "failed_to_load"]


class CaseExpectation(BaseModel):
    """Optional pass/fail criteria for a dataset case; absent for purely observational cases."""

    expected_overall_status: str | None = None
    expected_domain: str | None = None
    expected_min_confidence: float | None = None
    expect_halt: bool = False


class DatasetCase(BaseModel):
    """One prompt to evaluate, optionally tagged with a category and an expected outcome."""

    case_id: str
    prompt: str
    category: str | None = None
    expectation: CaseExpectation | None = None


class DatasetError(BaseModel):
    """A dataset row that could not be parsed into a DatasetCase at all (or a file that couldn't be opened)."""

    case_id: str | None = None
    raw_line_number: int | None = None
    error: str


class StageMetric(BaseModel):
    """A single stage's outcome and timing, extracted from one CompilationResult's stage_summaries."""

    stage_name: str
    status: str
    duration_ms: float
    confidence: float | None = None


class EvaluationReport(BaseModel):
    """The lightweight, per-case evaluation record produced immediately after one compilation.

    Deliberately holds no nested IntentIR/SystemDesign/DataSchema/ValidationReport — only the
    metrics extracted from them — so that streaming thousands of these costs megabytes, not
    gigabytes. The originating CompilationResult is discarded as soon as this report is built.
    """

    evaluation_id: str
    version: str
    case_id: str
    prompt: str
    category: str | None = None
    compilation_id: str
    overall_status: str
    final_decision: str
    stage_metrics: list[StageMetric] = Field(default_factory=list)
    validation_finding_counts: dict[str, int] = Field(default_factory=dict)
    failure_category: FailureCategory | None = None
    passed: bool | None = None
    notes: str | None = None
    total_duration_ms: float


class Distribution(BaseModel):
    """Streaming statistics for one numeric series; p50/p95 are deterministic approximations.

    Computed in O(1) memory via Welford's online algorithm (mean) and the P² algorithm
    (p50_approx/p95_approx) — never by sorting or retaining the underlying observations.
    """

    count: int
    mean: float
    min: float
    max: float
    p50_approx: float
    p95_approx: float


class BenchmarkResult(BaseModel):
    """The single O(1)-sized aggregate rollup produced once a dataset stream is exhausted.

    Deliberately carries no per-case list (e.g. no list of EvaluationReports or per-case
    outcomes) — that would reintroduce the exact O(n) memory growth this object exists to
    avoid. Per-case detail lives only in the streamed EvaluationReport output.
    """

    benchmark_id: str
    version: str
    dataset_name: str
    dataset_size: int
    compiler_version: str
    started_at: datetime
    completed_at: datetime
    total_duration_ms: float
    success_rate: float
    halt_rate: float
    error_rate: float
    validation_pass_rate: float
    confidence_by_stage: dict[str, Distribution] = Field(default_factory=dict)
    duration_by_stage_ms: dict[str, Distribution] = Field(default_factory=dict)
    failure_category_counts: dict[str, int] = Field(default_factory=dict)
    validation_finding_severity_counts: dict[str, int] = Field(default_factory=dict)
    dataset_categories: dict[str, int] = Field(default_factory=dict)
    dataset_errors: list[DatasetError] = Field(default_factory=list)
    status: BenchmarkStatus
