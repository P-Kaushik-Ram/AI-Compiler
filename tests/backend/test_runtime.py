"""Unit tests for the deterministic RuntimeService orchestrator."""
import pytest

from app.services.intent_extraction import IntentExtractionService
from app.services.runtime import RuntimeService
from app.services.system_design import SystemDesignService

runtime_service = RuntimeService()
intent_service = IntentExtractionService()
design_service = SystemDesignService()


def test_run_with_prompt_executes_all_four_stages_and_succeeds() -> None:
    """A clean CRM prompt should run all four stages, none skipped, and succeed with no findings."""
    result = runtime_service.run(prompt="Build a CRM where users can log in and manage contacts.")

    assert result.overall_status == "succeeded"
    assert result.final_decision == "proceed"
    assert result.error is None
    assert [s.stage_name for s in result.stage_summaries] == [
        "intent_extraction",
        "system_design",
        "schema_generation",
        "validation",
    ]
    assert all(s.status not in ("skipped", "error") for s in result.stage_summaries)
    assert result.intent_ir is not None
    assert result.system_design is not None
    assert result.data_schema is not None
    assert result.validation_report is not None
    assert result.validation_report.findings == []


def test_stage_durations_are_non_negative_and_total_covers_the_whole_run() -> None:
    """Every stage duration should be measured and the total duration should be at least their sum."""
    result = runtime_service.run(prompt="Build a CRM where users can log in and manage contacts.")

    assert all(s.duration_ms >= 0 for s in result.stage_summaries)
    assert result.total_duration_ms >= sum(s.duration_ms for s in result.stage_summaries)
    assert result.completed_at >= result.started_at


def test_empty_prompt_cascades_to_halted_overall_status() -> None:
    """An empty prompt should cascade through all four stages to a well-formed, halted result (not an error)."""
    result = runtime_service.run(prompt="")

    assert result.overall_status == "halted"
    assert result.final_decision == "halt"
    assert result.error is None
    assert len(result.stage_summaries) == 4
    assert result.validation_report is not None
    assert result.validation_report.status == "failed"


def test_resuming_from_a_pre_supplied_intent_ir_skips_stage_one() -> None:
    """Pre-supplying an IntentIR should skip Intent Extraction and resume from System Design."""
    ir = intent_service.extract("Build a CRM where users can log in and manage contacts.")

    result = runtime_service.run(intent_ir=ir)

    stage_statuses = {s.stage_name: s.status for s in result.stage_summaries}
    assert stage_statuses["intent_extraction"] == "skipped"
    assert stage_statuses["system_design"] == "complete"
    assert stage_statuses["schema_generation"] == "complete"
    assert stage_statuses["validation"] == "passed"
    assert result.intent_ir == ir
    assert result.overall_status == "succeeded"


def test_resuming_from_pre_supplied_intent_ir_and_system_design_skips_two_stages() -> None:
    """Pre-supplying both IntentIR and SystemDesign should skip the first two stages."""
    ir = intent_service.extract("Build a CRM where users can log in and manage contacts.")
    design = design_service.build(ir)

    result = runtime_service.run(intent_ir=ir, system_design=design)

    stage_statuses = {s.stage_name: s.status for s in result.stage_summaries}
    assert stage_statuses["intent_extraction"] == "skipped"
    assert stage_statuses["system_design"] == "skipped"
    assert stage_statuses["schema_generation"] == "complete"
    assert stage_statuses["validation"] == "passed"


def test_missing_prompt_and_intent_ir_returns_configuration_error_without_running_any_stage() -> None:
    """Calling run() with no prompt and no intent_ir must return an errored result, never raise."""
    result = runtime_service.run()

    assert result.overall_status == "errored"
    assert result.final_decision == "not_reached"
    assert result.stage_summaries == []
    assert "prompt" in result.error.lower() or "intent_ir" in result.error.lower()


def test_system_design_without_intent_ir_returns_configuration_error() -> None:
    """Supplying system_design without intent_ir is a contradictory configuration and must error cleanly.

    A prompt is also supplied so the 'prompt or intent_ir' check passes and the
    system_design-without-intent_ir check is the one actually exercised.
    """
    ir = intent_service.extract("Build a CRM where users can log in and manage contacts.")
    design = design_service.build(ir)

    result = runtime_service.run(prompt="Build a CRM where users can log in and manage contacts.", system_design=design)

    assert result.overall_status == "errored"
    assert "system_design" in result.error


def test_data_schema_without_system_design_returns_configuration_error() -> None:
    """Supplying data_schema without system_design is a contradictory configuration and must error cleanly."""
    ir = intent_service.extract("Build a CRM where users can log in and manage contacts.")
    design = design_service.build(ir)
    from app.services.schema_generation import SchemaGenerationService

    schema = SchemaGenerationService().generate(ir, design)

    result = runtime_service.run(intent_ir=ir, data_schema=schema)

    assert result.overall_status == "errored"
    assert "data_schema" in result.error


def test_unexpected_stage_exception_is_captured_not_raised(monkeypatch: pytest.MonkeyPatch) -> None:
    """If a stage raises unexpectedly, run() must capture it as data and never propagate the exception."""

    def _boom(self, prompt):
        raise RuntimeError("simulated extraction failure")

    monkeypatch.setattr("app.services.intent_extraction.IntentExtractionService.extract", _boom)

    result = runtime_service.run(prompt="Build a CRM where users can log in and manage contacts.")

    assert result.overall_status == "errored"
    assert result.final_decision == "not_reached"
    assert "simulated extraction failure" in result.error
    assert result.stage_summaries[-1].stage_name == "intent_extraction"
    assert result.stage_summaries[-1].status == "error"
    assert result.intent_ir is None
    assert result.validation_report is None


def test_unexpected_exception_in_a_later_stage_preserves_earlier_summaries(monkeypatch: pytest.MonkeyPatch) -> None:
    """A failure in System Design must preserve the already-completed Intent Extraction summary."""

    def _boom(self, intent_ir):
        raise RuntimeError("simulated design failure")

    monkeypatch.setattr("app.services.system_design.SystemDesignService.build", _boom)

    result = runtime_service.run(prompt="Build a CRM where users can log in and manage contacts.")

    assert result.overall_status == "errored"
    assert len(result.stage_summaries) == 2
    assert result.stage_summaries[0].stage_name == "intent_extraction"
    assert result.stage_summaries[0].status == "complete"
    assert result.stage_summaries[1].stage_name == "system_design"
    assert result.stage_summaries[1].status == "error"
    assert result.intent_ir is not None
    assert result.system_design is None
