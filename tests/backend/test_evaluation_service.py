"""Unit tests for EvaluationService: per-case evaluation, streaming batch execution, and scoring."""
from app.models.evaluation import CaseExpectation, DatasetCase, DatasetError
from app.services.evaluation import EvaluationService

service = EvaluationService()


def test_evaluate_case_returns_a_lightweight_report_for_a_successful_prompt() -> None:
    """A clean CRM prompt should evaluate to a 'succeeded' report with no failure_category."""
    case = DatasetCase(case_id="crm_001", prompt="Build a CRM where users can log in and manage contacts.")

    report = service.evaluate_case(case)

    assert report.case_id == "crm_001"
    assert report.overall_status == "succeeded"
    assert report.failure_category is None
    assert len(report.stage_metrics) == 4
    assert report.passed is None  # no expectation declared


def test_evaluate_case_classifies_a_vague_prompt_as_intent_ambiguous() -> None:
    """A prompt with no extractable entities should halt and classify as 'intent_ambiguous'."""
    case = DatasetCase(case_id="vague_001", prompt="Build me something cool.")

    report = service.evaluate_case(case)

    assert report.overall_status == "halted"
    assert report.failure_category == "intent_ambiguous"


def test_evaluate_case_with_expect_halt_expectation_passes_when_halted() -> None:
    """A case that declares expect_halt=True should be marked passed when the compiler does halt."""
    case = DatasetCase(
        case_id="vague_001",
        prompt="Build me something cool.",
        expectation=CaseExpectation(expect_halt=True),
    )

    report = service.evaluate_case(case)

    assert report.passed is True


def test_evaluate_case_with_expected_overall_status_mismatch_fails() -> None:
    """A case expecting 'succeeded' that actually halts should be marked passed=False."""
    case = DatasetCase(
        case_id="vague_001",
        prompt="Build me something cool.",
        expectation=CaseExpectation(expected_overall_status="succeeded"),
    )

    report = service.evaluate_case(case)

    assert report.passed is False


def test_evaluate_case_with_domain_mismatch_fails_and_notes_the_discrepancy() -> None:
    """A case expecting domain='healthcare' on a CRM prompt should fail with an explanatory note."""
    case = DatasetCase(
        case_id="crm_001",
        prompt="Build a CRM where users can log in and manage contacts.",
        expectation=CaseExpectation(expected_overall_status="succeeded", expected_domain="healthcare"),
    )

    report = service.evaluate_case(case)

    assert report.passed is False
    assert "domain" in report.notes


def test_evaluate_case_with_unreachable_confidence_threshold_fails() -> None:
    """An expected_min_confidence above what the compiler can ever produce should fail the case."""
    case = DatasetCase(
        case_id="crm_001",
        prompt="Build a CRM where users can log in and manage contacts.",
        expectation=CaseExpectation(expected_overall_status="succeeded", expected_min_confidence=0.999),
    )

    report = service.evaluate_case(case)

    assert report.passed is False
    assert "confidence" in report.notes


def test_run_benchmark_streams_reports_and_routes_dataset_errors_to_the_aggregator() -> None:
    """run_benchmark should yield one EvaluationReport per valid case and silently absorb DatasetErrors."""
    dataset = iter(
        [
            DatasetCase(case_id="crm_001", prompt="Build a CRM where users can log in and manage contacts."),
            DatasetError(case_id=None, raw_line_number=2, error="malformed row"),
            DatasetCase(case_id="todo_001", prompt="Build a to-do app where users can manage tasks."),
        ]
    )

    reports, aggregator = service.run_benchmark(dataset, dataset_name="mixed-batch")
    collected = list(reports)

    assert [r.case_id for r in collected] == ["crm_001", "todo_001"]

    result = aggregator.finalize()
    assert result.dataset_size == 2
    assert len(result.dataset_errors) == 1
    assert result.dataset_errors[0].raw_line_number == 2


def test_run_benchmark_from_path_evaluates_a_real_jsonl_file(tmp_path) -> None:
    """run_benchmark_from_path should stream a real file end-to-end and produce a correct BenchmarkResult."""
    dataset_file = tmp_path / "dataset.jsonl"
    dataset_file.write_text(
        '{"case_id": "crm_001", "prompt": "Build a CRM where users can log in and manage contacts."}\n'
        '{"case_id": "vague_001", "prompt": "Build me something cool."}\n',
        encoding="utf-8",
    )

    reports, aggregator = service.run_benchmark_from_path(dataset_file, dataset_name="file-batch")
    collected = list(reports)

    assert len(collected) == 2
    result = aggregator.finalize()
    assert result.status == "complete"
    assert result.dataset_size == 2


def test_run_benchmark_from_path_with_missing_file_yields_failed_to_load(tmp_path) -> None:
    """A nonexistent dataset path must produce a graceful 'failed_to_load' BenchmarkResult, not raise."""
    missing_path = tmp_path / "does_not_exist.jsonl"

    reports, aggregator = service.run_benchmark_from_path(missing_path, dataset_name="missing-file")
    collected = list(reports)

    assert collected == []
    result = aggregator.finalize()
    assert result.status == "failed_to_load"
    assert result.dataset_size == 0
    assert len(result.dataset_errors) == 1
