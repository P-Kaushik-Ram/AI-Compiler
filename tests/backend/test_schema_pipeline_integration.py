"""Integration tests proving Prompt -> Intent Extraction -> System Design -> Schema Generation works end-to-end."""
from app.services.intent_extraction import IntentExtractionService
from app.services.schema_generation import SchemaGenerationService
from app.services.system_design import SystemDesignService

intent_service = IntentExtractionService()
design_service = SystemDesignService()
schema_service = SchemaGenerationService()


def test_crm_prompt_flows_through_all_three_stages() -> None:
    """A CRM prompt should produce a complete IR, design, and schema, all traceable to one another."""
    prompt = "Build a CRM where users can log in and manage contacts."

    ir = intent_service.extract(prompt)
    assert ir.status == "complete"

    design = design_service.build(ir)
    assert design.status == "complete"
    assert design.source_intent_id == ir.intent_id

    schema = schema_service.generate(ir, design)
    assert schema.status == "complete"
    assert schema.source_intent_id == ir.intent_id
    assert schema.source_design_id == design.design_id
    assert {"user", "contact"} == {e.name for e in schema.entities}


def test_todo_prompt_flows_through_all_three_stages_with_foreign_key() -> None:
    """A to-do prompt should flow through all three stages and produce a User->Todo foreign key relationship."""
    prompt = (
        "I want a simple app where users can sign up, log in, and manage a to-do list. "
        "Only logged-in users should see their own todos."
    )

    ir = intent_service.extract(prompt)
    design = design_service.build(ir)
    schema = schema_service.generate(ir, design)

    assert schema.status == "complete"
    relationship = next(r for r in schema.relationships if r.name == "user_owns_todo")
    assert relationship.foreign_key_field == "user_id"


def test_vague_prompt_is_rejected_before_schema_fabricates_structure() -> None:
    """A vague prompt that needs clarification at Stage 1 must short-circuit Stage 3 rather than guess."""
    ir = intent_service.extract("Build me something cool.")
    assert ir.status == "needs_clarification"

    design = design_service.build(ir)
    assert design.status == "rejected"

    schema = schema_service.generate(ir, design)
    assert schema.status == "rejected"
    assert schema.entities == []
