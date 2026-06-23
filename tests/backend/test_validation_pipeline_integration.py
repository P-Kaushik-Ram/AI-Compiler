"""Integration tests proving Prompt -> Intent Extraction -> System Design -> Schema Generation -> Validation
works end-to-end across all four completed compiler stages."""
from app.services.intent_extraction import IntentExtractionService
from app.services.schema_generation import SchemaGenerationService
from app.services.system_design import SystemDesignService
from app.services.validation import ValidationService

intent_service = IntentExtractionService()
design_service = SystemDesignService()
schema_service = SchemaGenerationService()
validation_service = ValidationService()


def test_crm_prompt_flows_through_all_four_stages_and_passes() -> None:
    """A CRM prompt should flow cleanly through all four stages and validate with no findings."""
    prompt = "Build a CRM where users can log in and manage contacts."

    ir = intent_service.extract(prompt)
    assert ir.status == "complete"

    design = design_service.build(ir)
    assert design.status == "complete"

    schema = schema_service.generate(ir, design)
    assert schema.status == "complete"

    report = validation_service.validate(ir, design, schema)
    assert report.status == "passed"
    assert report.pipeline_decision == "proceed"
    assert report.findings == []
    assert report.source_intent_id == ir.intent_id
    assert report.source_design_id == design.design_id
    assert report.source_schema_id == schema.schema_id


def test_todo_prompt_flows_through_all_four_stages_and_passes() -> None:
    """A to-do prompt (with an ownership relationship and a foreign key) should validate cleanly end-to-end."""
    prompt = (
        "I want a simple app where users can sign up, log in, and manage a to-do list. "
        "Only logged-in users should see their own todos."
    )

    ir = intent_service.extract(prompt)
    design = design_service.build(ir)
    schema = schema_service.generate(ir, design)
    report = validation_service.validate(ir, design, schema)

    assert report.status == "passed"
    assert report.pipeline_decision == "proceed"
    assert report.consistency_summary.relationships_checked == 1


def test_vague_prompt_cascades_to_a_failed_validation_report() -> None:
    """A vague prompt that needs clarification at Stage 1 should cascade through every stage to a failed report."""
    ir = intent_service.extract("Build me something cool.")
    assert ir.status == "needs_clarification"

    design = design_service.build(ir)
    assert design.status == "rejected"

    schema = schema_service.generate(ir, design)
    assert schema.status == "rejected"

    report = validation_service.validate(ir, design, schema)
    assert report.status == "failed"
    assert report.pipeline_decision == "halt"
    assert any(f.category == "cross_stage_inconsistency" for f in report.findings)
