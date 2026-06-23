"""Unit tests for the O(1)-memory StreamingAggregator, Welford mean, and P2 quantile estimator."""
import random

from app.models.evaluation import DatasetError, EvaluationReport, StageMetric
from app.services.evaluation_aggregator import (
    FAILURE_CATEGORIES,
    FINDING_SEVERITIES,
    STAGE_NAMES,
    StreamingAggregator,
    _P2QuantileEstimator,
    _WelfordAccumulator,
)


def _make_report(
    case_id: str,
    overall_status: str,
    category: str | None = None,
    failure_category: str | None = None,
    duration_ms: float = 1.0,
    confidence: float = 0.9,
    validation_severities: dict[str, int] | None = None,
) -> EvaluationReport:
    """Build a minimal EvaluationReport for aggregator tests without running the real compiler."""
    return EvaluationReport(
        evaluation_id="eval-test",
        version="1.0",
        case_id=case_id,
        prompt="irrelevant for aggregator tests",
        category=category,
        compilation_id="compilation-test",
        overall_status=overall_status,
        final_decision="proceed",
        stage_metrics=[
            StageMetric(stage_name=name, status="complete", duration_ms=duration_ms, confidence=confidence)
            for name in STAGE_NAMES
        ],
        validation_finding_counts=validation_severities or {},
        failure_category=failure_category,
        passed=None,
        notes=None,
        total_duration_ms=duration_ms * len(STAGE_NAMES),
    )


def test_welford_accumulator_computes_correct_running_mean() -> None:
    """Welford's algorithm should produce the same mean as a naive sum/count over the same series."""
    values = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
    accumulator = _WelfordAccumulator()
    for value in values:
        accumulator.update(value)

    assert accumulator.count == len(values)
    assert accumulator.mean == sum(values) / len(values)


def test_p2_estimator_converges_near_true_quantiles_on_a_known_distribution() -> None:
    """The P2 estimator should land close to the true p50/p95 of a known, shuffled distribution."""
    values = list(range(1, 101))
    random.Random(42).shuffle(values)

    p50 = _P2QuantileEstimator(0.5)
    p95 = _P2QuantileEstimator(0.95)
    for value in values:
        p50.update(float(value))
        p95.update(float(value))

    assert 45.0 <= p50.estimate() <= 55.0
    assert 90.0 <= p95.estimate() <= 100.0


def test_p2_estimator_is_deterministic_for_the_same_input_sequence() -> None:
    """Feeding the identical sequence twice must produce bit-for-bit identical estimates."""
    values = [3.0, 1.0, 4.0, 1.0, 5.0, 9.0, 2.0, 6.0, 5.0, 3.0, 5.0]

    first = _P2QuantileEstimator(0.5)
    second = _P2QuantileEstimator(0.5)
    for value in values:
        first.update(value)
    for value in values:
        second.update(value)

    assert first.estimate() == second.estimate()


def test_p2_estimator_falls_back_to_exact_median_below_five_samples() -> None:
    """With fewer than 5 observations, the estimator should return the exact median of what it has."""
    estimator = _P2QuantileEstimator(0.5)
    for value in (10.0, 20.0, 30.0):
        estimator.update(value)

    assert estimator.estimate() == 20.0


def test_streaming_aggregator_computes_correct_rates_and_categories() -> None:
    """A small mixed batch should produce exactly the expected rates, counts, and category tallies."""
    aggregator = StreamingAggregator(dataset_name="unit-test", compiler_version="1.0")

    aggregator.update(_make_report("c1", "succeeded", category="crm"))
    aggregator.update(_make_report("c2", "succeeded_with_warnings", category="crm"))
    aggregator.update(_make_report("c3", "halted", category="ambiguous", failure_category="intent_ambiguous"))
    aggregator.update(_make_report("c4", "errored", failure_category="infrastructure_error"))

    result = aggregator.finalize()

    assert result.dataset_size == 4
    assert result.success_rate == 0.5
    assert result.halt_rate == 0.25
    assert result.error_rate == 0.25
    assert result.dataset_categories == {"crm": 2, "ambiguous": 1, "uncategorized": 1}
    assert result.failure_category_counts["intent_ambiguous"] == 1
    assert result.failure_category_counts["infrastructure_error"] == 1
    assert set(result.failure_category_counts) == set(FAILURE_CATEGORIES)
    assert result.status == "complete"


def test_streaming_aggregator_tallies_validation_finding_severities() -> None:
    """Per-case validation_finding_counts should sum correctly into the aggregate severity tallies."""
    aggregator = StreamingAggregator(dataset_name="unit-test", compiler_version="1.0")
    aggregator.update(_make_report("c1", "succeeded", validation_severities={"warning": 2, "critical": 1}))
    aggregator.update(_make_report("c2", "succeeded", validation_severities={"warning": 1}))

    result = aggregator.finalize()

    assert result.validation_finding_severity_counts["warning"] == 3
    assert result.validation_finding_severity_counts["critical"] == 1
    assert result.validation_finding_severity_counts["info"] == 0
    assert set(result.validation_finding_severity_counts) == set(FINDING_SEVERITIES)


def test_streaming_aggregator_records_dataset_errors_without_affecting_compiler_metrics() -> None:
    """Dataset parse errors must be tracked separately and must not count toward dataset_size."""
    aggregator = StreamingAggregator(dataset_name="unit-test", compiler_version="1.0")
    aggregator.update(_make_report("c1", "succeeded"))
    aggregator.record_dataset_error(DatasetError(case_id=None, raw_line_number=7, error="Invalid JSON"))

    result = aggregator.finalize()

    assert result.dataset_size == 1
    assert len(result.dataset_errors) == 1
    assert result.dataset_errors[0].raw_line_number == 7


def test_streaming_aggregator_mark_failed_to_load_short_circuits_status() -> None:
    """A dataset that could not be opened at all must finalize to status='failed_to_load'."""
    aggregator = StreamingAggregator(dataset_name="unit-test", compiler_version="1.0")
    aggregator.mark_failed_to_load("file not found")

    result = aggregator.finalize()

    assert result.status == "failed_to_load"
    assert result.dataset_size == 0
    assert len(result.dataset_errors) == 1


def test_streaming_aggregator_omits_distributions_for_stages_with_no_observations() -> None:
    """A report with no stage_metrics at all should not produce phantom zero-count distributions."""
    aggregator = StreamingAggregator(dataset_name="unit-test", compiler_version="1.0")
    empty_report = EvaluationReport(
        evaluation_id="eval-empty",
        version="1.0",
        case_id="c1",
        prompt="x",
        compilation_id="compilation-empty",
        overall_status="errored",
        final_decision="not_reached",
        stage_metrics=[],
        failure_category="infrastructure_error",
        total_duration_ms=0.0,
    )
    aggregator.update(empty_report)

    result = aggregator.finalize()

    assert result.confidence_by_stage == {}
    assert result.duration_by_stage_ms == {}
    assert result.validation_pass_rate == 0.0
