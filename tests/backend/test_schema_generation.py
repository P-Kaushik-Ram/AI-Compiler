"""Unit tests for the deterministic SchemaGenerationService."""
from app.models.intent import Action, Attribute, Entity, IntentIR, Relationship, UserStory
from app.services.intent_extraction import IntentExtractionService
from app.services.schema_generation import SchemaGenerationService
from app.services.system_design import SystemDesignService

intent_service = IntentExtractionService()
design_service = SystemDesignService()
schema_service = SchemaGenerationService()


def _build(prompt: str):
    """Run a prompt through Stage 1 and Stage 2, returning (IntentIR, SystemDesign)."""
    ir = intent_service.extract(prompt)
    design = design_service.build(ir)
    return ir, design


def test_crm_schema_has_user_and_contact_entities_with_traceable_fields() -> None:
    """A CRM IntentIR+SystemDesign should produce user/contact schema entities with correct field shapes."""
    ir, design = _build("Build a CRM where users can log in and manage contacts.")
    schema = schema_service.generate(ir, design)

    assert schema.status == "complete"
    assert schema.source_intent_id == ir.intent_id
    assert schema.source_design_id == design.design_id

    entity_names = {e.name for e in schema.entities}
    assert {"user", "contact"} == entity_names

    user_entity = next(e for e in schema.entities if e.name == "user")
    assert user_entity.module == "Authentication"
    assert any(f.name == "id" and f.is_primary_key and f.data_type == "uuid" for f in user_entity.fields)
    email_field = next(f for f in user_entity.fields if f.name == "email")
    assert email_field.is_unique is True
    assert email_field.is_sensitive is True
    password_field = next(f for f in user_entity.fields if f.name == "password")
    assert password_field.is_sensitive is True


def test_todo_schema_generates_foreign_key_from_ownership_relationship() -> None:
    """An ownership relationship (User owns Todo) should produce a one_to_many relationship with a FK field."""
    prompt = (
        "I want a simple app where users can sign up, log in, and manage a to-do list. "
        "Only logged-in users should see their own todos."
    )
    ir, design = _build(prompt)
    schema = schema_service.generate(ir, design)

    assert schema.status == "complete"
    relationship = next(r for r in schema.relationships if r.name == "user_owns_todo")
    assert relationship.cardinality == "one_to_many"
    assert relationship.foreign_key_field == "user_id"
    assert relationship.from_entity == "user"
    assert relationship.to_entity == "todo"


def test_ecommerce_schema_marks_payment_fields_sensitive() -> None:
    """E-commerce payment risk (sensitivity propagation) should mark Payment entity fields as sensitive.

    The rule-based extractor always tags 'payments' risk as 'medium' severity (see Stage 1), and the
    approved design only generates SchemaConstraints for 'high'/'critical' risks, so this prompt is
    expected to propagate sensitivity but not produce a constraint; the healthcare test below covers
    the high-severity constraint-generation path.
    """
    prompt = (
        "Build an e-commerce store. Customers can manage orders and payments. "
        "Payment must be confirmed before an order is created."
    )
    ir, design = _build(prompt)
    schema = schema_service.generate(ir, design)

    assert schema.status == "complete"
    payment_entity = next(e for e in schema.entities if e.name == "payment")
    assert any(f.is_sensitive for f in payment_entity.fields)


def test_healthcare_schema_adds_encryption_and_audit_constraints_for_patient() -> None:
    """A healthcare IntentIR/SystemDesign with medical_data + compliance risks should constrain Patient data."""
    prompt = (
        "Build a healthcare clinic system to manage patients, doctors, and appointments. "
        "This system must comply with HIPAA regulations."
    )
    ir, design = _build(prompt)
    schema = schema_service.generate(ir, design)

    assert schema.status == "complete"
    patient_entity = next(e for e in schema.entities if e.name == "patient")
    assert all(f.is_sensitive for f in patient_entity.fields if f.name != "id")

    constraint_types_for_patient = {
        c.constraint_type for c in schema.constraints if c.entity == "patient"
    }
    assert "requires_encryption" in constraint_types_for_patient
    assert "requires_audit_log" in constraint_types_for_patient


def test_rejected_system_design_produces_rejected_schema() -> None:
    """A SystemDesign that is itself rejected must not be schema-generated on top of."""
    ir, design = _build("")
    assert design.status == "rejected"

    schema = schema_service.generate(ir, design)

    assert schema.status == "rejected"
    assert schema.confidence == 0.0
    assert schema.entities == []
    assert schema.schema_ambiguities[0].severity == "blocking"


def test_conflicting_relationship_types_flagged_as_blocking_ambiguity() -> None:
    """Two relationships between the same entity pair with different types must block, not guess."""
    ir = IntentIR(
        intent_id="manual-conflict-001",
        version="1.0",
        domain="general",
        primary_intent="build_app",
        domain_summary="A manual IR with conflicting relationship types.",
        entities=[
            Entity(name="Author", description="A writer", attributes=[], confidence=0.9),
            Entity(name="Book", description="A written work", attributes=[], confidence=0.9),
        ],
        relationships=[
            Relationship(from_entity="Author", to_entity="Book", relationship_type="owns", description="Author owns Book"),
            Relationship(
                from_entity="Author",
                to_entity="Book",
                relationship_type="associated_with",
                description="Author associated with Book",
            ),
        ],
        actions=[Action(name="create_book", target_entity="Book", description="Add a book", confidence=0.9)],
        user_stories=[UserStory(actor="User", goal="create a book", priority="must_have", related_action="create_book")],
        confidence=0.9,
        status="complete",
        raw_prompt="manual test",
    )
    design = design_service.build(ir)
    schema = schema_service.generate(ir, design)

    assert schema.status == "needs_clarification"
    assert any(a.severity == "blocking" and "Conflicting relationship types" in a.question for a in schema.schema_ambiguities)
    assert not any({r.from_entity, r.to_entity} == {"author", "book"} for r in schema.relationships)


def test_unknown_type_hint_defaults_to_string_with_advisory_ambiguity() -> None:
    """An attribute with an unrecognized type_hint should default to 'string' and raise an advisory ambiguity."""
    ir = IntentIR(
        intent_id="manual-unknown-type-001",
        version="1.0",
        domain="general",
        primary_intent="build_app",
        domain_summary="A manual IR with an unknown attribute type_hint.",
        entities=[
            Entity(
                name="Widget",
                description="A test entity",
                attributes=[Attribute(name="payload", type_hint="json", is_optional=True)],
                confidence=0.9,
            )
        ],
        actions=[Action(name="create_widget", target_entity="Widget", description="Add a widget", confidence=0.9)],
        user_stories=[UserStory(actor="User", goal="create a widget", priority="must_have", related_action="create_widget")],
        confidence=0.9,
        status="complete",
        raw_prompt="manual test",
    )
    design = design_service.build(ir)
    schema = schema_service.generate(ir, design)

    assert schema.status == "complete"
    widget_entity = next(e for e in schema.entities if e.name == "widget")
    payload_field = next(f for f in widget_entity.fields if f.name == "payload")
    assert payload_field.data_type == "string"
    assert any(
        a.severity == "advisory" and "Unknown type_hint" in a.question for a in schema.schema_ambiguities
    )
