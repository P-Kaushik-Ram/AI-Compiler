"""Unit tests for the deterministic IntentExtractionService."""
from app.services.intent_extraction import IntentExtractionService

service = IntentExtractionService()


def test_crm_prompt_detects_domain_entities_and_auth() -> None:
    """A CRM prompt should yield the crm domain, Contact/User entities, and an auth NFR."""
    ir = service.extract("Build a CRM with login and contacts.")

    assert ir.domain == "crm"
    assert ir.status == "complete"
    entity_names = {e.name for e in ir.entities}
    assert "Contact" in entity_names
    assert "User" in entity_names
    action_names = {a.name for a in ir.actions}
    assert "log_in" in action_names
    assert any(nfr.category == "auth" for nfr in ir.non_functional_requirements)


def test_todo_app_prompt_detects_crud_and_ownership() -> None:
    """A to-do prompt with 'manage' and ownership language should produce CRUD actions and an owns relationship."""
    prompt = (
        "I want a simple app where users can sign up, log in, and manage a to-do list. "
        "Only logged-in users should see their own todos."
    )
    ir = service.extract(prompt)

    assert ir.domain == "productivity"
    assert ir.status == "complete"
    entity_names = {e.name for e in ir.entities}
    assert "Todo" in entity_names
    assert "User" in entity_names
    action_names = {a.name for a in ir.actions}
    assert {"create_todo", "update_todo", "delete_todo", "list_todo"}.issubset(action_names)
    assert any(
        rel.from_entity == "User" and rel.to_entity == "Todo" and rel.relationship_type == "owns"
        for rel in ir.relationships
    )
    assert any(a.affected_field == "actions" for a in ir.assumptions)


def test_empty_prompt_is_rejected() -> None:
    """An empty or whitespace-only prompt must be rejected with zero confidence and no fabricated structure."""
    ir = service.extract("   ")

    assert ir.status == "rejected"
    assert ir.confidence == 0.0
    assert ir.entities == []
    assert ir.actions == []
    assert len(ir.ambiguities) == 1
    assert ir.ambiguities[0].severity == "blocking"


def test_ambiguous_prompt_with_conflicting_auth_statements_needs_clarification() -> None:
    """Conflicting auth statements ('no login' plus 'log in') must produce a blocking ambiguity."""
    prompt = "Build an app with no login required, but users can log in with their email to manage orders."
    ir = service.extract(prompt)

    assert ir.status == "needs_clarification"
    assert any(a.severity == "blocking" for a in ir.ambiguities)
    assert ir.confidence < 0.95


def test_vague_prompt_with_no_entities_is_blocking() -> None:
    """A prompt with no recognizable entities or actions should be flagged as a blocking ambiguity."""
    ir = service.extract("Build me something cool.")

    assert ir.status == "needs_clarification"
    assert ir.entities == []
    assert any(flag.category == "high_ambiguity" for flag in ir.risk_flags)
