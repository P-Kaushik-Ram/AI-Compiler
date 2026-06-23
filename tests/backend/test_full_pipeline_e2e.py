"""End-to-end tests proving the full compiler (Stages 1-5) works correctly via RuntimeService alone."""
from app.services.runtime import RuntimeService

runtime_service = RuntimeService()


def test_crm_prompt_compiles_successfully_end_to_end() -> None:
    """A CRM prompt should compile cleanly through every stage with zero validation findings."""
    result = runtime_service.run(prompt="Build a CRM where users can log in and manage contacts.")

    assert result.overall_status == "succeeded"
    assert result.final_decision == "proceed"
    entity_names = {e.name for e in result.data_schema.entities}
    assert {"user", "contact"} == entity_names
    assert result.validation_report.findings == []


def test_todo_prompt_compiles_successfully_with_ownership_relationship() -> None:
    """A to-do prompt should compile end-to-end and produce a traceable User->Todo foreign key."""
    prompt = (
        "I want a simple app where users can sign up, log in, and manage a to-do list. "
        "Only logged-in users should see their own todos."
    )

    result = runtime_service.run(prompt=prompt)

    assert result.overall_status == "succeeded"
    relationship = next(r for r in result.data_schema.relationships if r.name == "user_owns_todo")
    assert relationship.foreign_key_field == "user_id"
    assert result.validation_report.status == "passed"


def test_ecommerce_prompt_compiles_successfully_with_sensitivity_propagated() -> None:
    """An e-commerce prompt should compile end-to-end with Payment fields marked sensitive."""
    prompt = (
        "Build an e-commerce store. Customers can manage orders and payments. "
        "Payment must be confirmed before an order is created."
    )

    result = runtime_service.run(prompt=prompt)

    assert result.overall_status == "succeeded"
    payment_entity = next(e for e in result.data_schema.entities if e.name == "payment")
    assert any(f.is_sensitive for f in payment_entity.fields)
    assert len(result.system_design.workflows) == 1


def test_healthcare_prompt_compiles_successfully_with_high_severity_risks() -> None:
    """A healthcare prompt should compile end-to-end with high-severity risks fully propagated to constraints."""
    prompt = (
        "Build a healthcare clinic system to manage patients, doctors, and appointments. "
        "This system must comply with HIPAA regulations."
    )

    result = runtime_service.run(prompt=prompt)

    assert result.overall_status == "succeeded"
    constraint_types_for_patient = {c.constraint_type for c in result.data_schema.constraints if c.entity == "patient"}
    assert "requires_encryption" in constraint_types_for_patient
    assert "requires_audit_log" in constraint_types_for_patient
    assert result.validation_report.findings == []


def test_vague_prompt_halts_cleanly_end_to_end_without_fabricating_structure() -> None:
    """A vague prompt should cascade through every stage to a clean halt, with no fabricated entities."""
    result = runtime_service.run(prompt="Build me something cool.")

    assert result.overall_status == "halted"
    assert result.final_decision == "halt"
    assert result.error is None
    assert result.intent_ir.entities == []
    assert result.system_design.modules == []
    assert result.data_schema.entities == []
    assert result.validation_report.status == "failed"


def test_every_stage_summary_traces_to_the_same_compilation_across_a_full_run() -> None:
    """All four stage summaries should be present, in order, each carrying a real measured duration."""
    result = runtime_service.run(prompt="Build a CRM where users can log in and manage contacts.")

    assert len(result.stage_summaries) == 4
    for summary in result.stage_summaries:
        assert summary.duration_ms >= 0
        assert summary.summary != ""
    assert result.data_schema.source_intent_id == result.intent_ir.intent_id
    assert result.data_schema.source_design_id == result.system_design.design_id
    assert result.validation_report.source_schema_id == result.data_schema.schema_id
