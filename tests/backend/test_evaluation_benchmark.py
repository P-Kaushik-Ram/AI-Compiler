"""Benchmark-scale tests: correctness and determinism of the Evaluation Framework over a larger dataset.

These don't measure wall-clock performance; they prove that streaming a few hundred cases through
EvaluationService produces internally-consistent aggregate metrics and that re-running the same
dataset twice yields identical non-timing results, exactly as the streaming design requires.
"""
from app.models.evaluation import DatasetCase
from app.services.evaluation import EvaluationService

PROMPT_TEMPLATES: tuple[tuple[str, str], ...] = (
    ("crm", "Build a CRM where users can log in and manage contacts."),
    (
        "productivity",
        "I want a simple app where users can sign up, log in, and manage a to-do list. "
        "Only logged-in users should see their own todos.",
    ),
    (
        "ecommerce",
        "Build an e-commerce store. Customers can manage orders and payments. "
        "Payment must be confirmed before an order is created.",
    ),
    (
        "healthcare",
        "Build a healthcare clinic system to manage patients, doctors, and appointments. "
        "This system must comply with HIPAA regulations.",
    ),
    ("ambiguous", "Build me something cool."),
)


def _build_dataset(size: int) -> list[DatasetCase]:
    """Build a synthetic dataset of the given size by cycling through the fixed prompt templates."""
    cases = []
    for index in range(size):
        category, prompt = PROMPT_TEMPLATES[index % len(PROMPT_TEMPLATES)]
        cases.append(DatasetCase(case_id=f"case_{index:04d}", prompt=prompt, category=category))
    return cases


def test_benchmark_over_two_hundred_cases_produces_internally_consistent_aggregates() -> None:
    """A 200-case synthetic benchmark should produce counts and rates that are mutually consistent."""
    service = EvaluationService()
    dataset = _build_dataset(200)

    reports, aggregator = service.run_benchmark(iter(dataset), dataset_name="benchmark-200")
    collected = list(reports)
    result = aggregator.finalize()

    assert len(collected) == 200
    assert result.dataset_size == 200

    expected_per_category = 200 // len(PROMPT_TEMPLATES)
    assert all(count == expected_per_category for count in result.dataset_categories.values())
    assert sum(result.dataset_categories.values()) == 200

    # 1 of every 5 templates ("ambiguous") halts; the rest succeed.
    assert result.halt_rate == 0.2
    assert result.success_rate == 0.8
    assert result.failure_category_counts["intent_ambiguous"] == 40

    for distribution in result.duration_by_stage_ms.values():
        assert distribution.count == 200
        assert distribution.min <= distribution.p50_approx <= distribution.max
        assert distribution.min <= distribution.p95_approx <= distribution.max


def test_benchmark_is_deterministic_across_repeated_runs_excluding_timing() -> None:
    """Running the identical dataset twice must yield identical classification metrics, every time."""
    service = EvaluationService()

    dataset_a = _build_dataset(60)
    reports_a, aggregator_a = service.run_benchmark(iter(dataset_a), dataset_name="determinism-check")
    list(reports_a)
    result_a = aggregator_a.finalize()

    dataset_b = _build_dataset(60)
    reports_b, aggregator_b = service.run_benchmark(iter(dataset_b), dataset_name="determinism-check")
    list(reports_b)
    result_b = aggregator_b.finalize()

    assert result_a.dataset_size == result_b.dataset_size
    assert result_a.success_rate == result_b.success_rate
    assert result_a.halt_rate == result_b.halt_rate
    assert result_a.error_rate == result_b.error_rate
    assert result_a.failure_category_counts == result_b.failure_category_counts
    assert result_a.dataset_categories == result_b.dataset_categories
    assert result_a.validation_finding_severity_counts == result_b.validation_finding_severity_counts

    # duration_ms is real measured wall-clock timing — the one sanctioned exception to determinism
    # throughout this project — so only its *count* is asserted here, not its value.
    for stage_name in result_a.duration_by_stage_ms:
        assert result_a.duration_by_stage_ms[stage_name].count == result_b.duration_by_stage_ms[stage_name].count

    # confidence is produced by deterministic rule-based extraction logic, not timing, so its
    # full distribution (including the P2 percentile estimates) must match exactly across runs.
    for stage_name in result_a.confidence_by_stage:
        dist_a = result_a.confidence_by_stage[stage_name]
        dist_b = result_b.confidence_by_stage[stage_name]
        assert dist_a == dist_b


def test_evaluation_report_stream_never_grows_the_aggregator_state_object() -> None:
    """The aggregator's tracked dictionaries must stay fixed-size (stage/category/severity counts only)."""
    service = EvaluationService()
    dataset = _build_dataset(150)

    reports, aggregator = service.run_benchmark(iter(dataset), dataset_name="fixed-size-check")
    for _ in reports:
        pass

    # Internal dicts are keyed by the fixed stage-name/failure-category/severity taxonomies,
    # never by case_id or any other per-case identifier — so their key counts are bounded
    # regardless of how many of the 150 cases were processed.
    assert len(aggregator._duration_accumulators) == 4
    assert len(aggregator._confidence_accumulators) == 4
    assert len(aggregator._failure_category_counts) == 5
    assert len(aggregator._validation_severity_counts) == 4
    # dataset_categories is bounded by distinct categories actually present (5 here), not by 150.
    assert len(aggregator._dataset_categories) == len(PROMPT_TEMPLATES)
