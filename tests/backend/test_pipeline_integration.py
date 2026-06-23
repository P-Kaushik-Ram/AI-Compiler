"""Integration tests proving Prompt -> Intent Extraction -> System Design works end-to-end."""
from app.services.intent_extraction import IntentExtractionService
from app.services.system_design import SystemDesignService

intent_service = IntentExtractionService()
design_service = SystemDesignService()


def test_crm_prompt_flows_through_both_stages() -> None:
    """A CRM prompt should produce a complete IntentIR and a complete, traceable SystemDesign."""
    prompt = "Build a CRM where users can log in and manage contacts."

    ir = intent_service.extract(prompt)
    assert ir.status == "complete"

    design = design_service.build(ir)
    assert design.status == "complete"
    assert design.source_intent_id == ir.intent_id
    assert {"Authentication", "Contact Management"}.issubset({m.name for m in design.modules})


def test_todo_prompt_flows_through_both_stages() -> None:
    """A to-do prompt should flow through extraction into a design with an ownership-based dependency."""
    prompt = (
        "I want a simple app where users can sign up, log in, and manage a to-do list. "
        "Only logged-in users should see their own todos."
    )

    ir = intent_service.extract(prompt)
    assert ir.status == "complete"

    design = design_service.build(ir)
    assert design.status == "complete"
    assert design.source_intent_id == ir.intent_id
    assert any(
        dep.from_module == "Todo Management" and dep.to_module == "Authentication"
        for dep in design.module_dependencies
    )


def test_vague_prompt_is_rejected_before_design_fabricates_structure() -> None:
    """A vague prompt that needs clarification at Stage 1 must short-circuit Stage 2 rather than guess."""
    ir = intent_service.extract("Build me something cool.")
    assert ir.status == "needs_clarification"

    design = design_service.build(ir)
    assert design.status == "rejected"
    assert design.modules == []
