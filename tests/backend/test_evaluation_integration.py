"""Integration tests proving the Evaluation Framework correctly drives the full compiler pipeline.

Also enforces the architectural constraint that the framework consumes RuntimeService only.
"""
import app.services.evaluation as evaluation_module
from app.models.evaluation import CaseExpectation, DatasetCase
from app.services.evaluation import EvaluationService

service = EvaluationService()


def test_evaluation_service_never_imports_individual_stage_services() -> None:
    """Architectural guard rail: the Evaluation Framework must consume RuntimeService only.

    If app.services.evaluation ever starts importing IntentExtractionService, SystemDesignService,
    SchemaGenerationService, or ValidationService directly, this test fails immediately.
    """
    forbidden = {"IntentExtractionService", "SystemDesignService", "SchemaGenerationService", "ValidationService"}
    imported_names = set(vars(evaluation_module).keys())

    assert forbidden.isdisjoint(imported_names)


def test_evaluation_framework_drives_a_mixed_dataset_through_the_full_five_stage_pipeline() -> None:
    """A small, realistic dataset (crm/todo/ecommerce/healthcare/vague) should evaluate correctly end-to-end."""
    dataset = iter(
        [
            DatasetCase(
                case_id="crm_001",
                prompt="Build a CRM where users can log in and manage contacts.",
                category="crm",
                expectation=CaseExpectation(expected_overall_status="succeeded"),
            ),
            DatasetCase(
                case_id="todo_001",
                prompt="I want a simple app where users can sign up, log in, and manage a to-do list. "
                "Only logged-in users should see their own todos.",
                category="productivity",
                expectation=CaseExpectation(expected_overall_status="succeeded"),
            ),
            DatasetCase(
                case_id="ecommerce_001",
                prompt="Build an e-commerce store. Customers can manage orders and payments. "
                "Payment must be confirmed before an order is created.",
                category="ecommerce",
            ),
            DatasetCase(
                case_id="healthcare_001",
                prompt="Build a healthcare clinic system to manage patients, doctors, and appointments. "
                "This system must comply with HIPAA regulations.",
                category="healthcare",
            ),
            DatasetCase(
                case_id="vague_001",
                prompt="Build me something cool.",
                category="ambiguous",
                expectation=CaseExpectation(expect_halt=True),
            ),
        ]
    )

    reports, aggregator = service.run_benchmark(dataset, dataset_name="integration-mixed")
    collected = list(reports)

    assert len(collected) == 5
    by_case_id = {report.case_id: report for report in collected}
    assert by_case_id["crm_001"].passed is True
    assert by_case_id["todo_001"].passed is True
    assert by_case_id["vague_001"].passed is True
    assert by_case_id["vague_001"].failure_category == "intent_ambiguous"
    assert by_case_id["healthcare_001"].overall_status == "succeeded"

    result = aggregator.finalize()
    assert result.dataset_size == 5
    assert result.success_rate == 0.8
    assert result.halt_rate == 0.2
    assert result.dataset_categories == {
        "crm": 1,
        "productivity": 1,
        "ecommerce": 1,
        "healthcare": 1,
        "ambiguous": 1,
    }
    assert result.failure_category_counts["intent_ambiguous"] == 1
    assert "intent_extraction" in result.duration_by_stage_ms
    assert "validation" in result.confidence_by_stage


def test_evaluation_compilation_results_are_never_retained_on_the_report() -> None:
    """EvaluationReport must carry no nested compiler artifact, only the metrics extracted from one."""
    case = DatasetCase(case_id="crm_001", prompt="Build a CRM where users can log in and manage contacts.")

    report = service.evaluate_case(case)

    dumped = report.model_dump()
    assert "intent_ir" not in dumped
    assert "system_design" not in dumped
    assert "data_schema" not in dumped
    assert "validation_report" not in dumped
