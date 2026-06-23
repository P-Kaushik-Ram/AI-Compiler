"""Unit tests for the deterministic ValidationService."""
from app.services.intent_extraction import IntentExtractionService
from app.services.schema_generation import SchemaGenerationService
from app.services.system_design import SystemDesignService
from app.services.validation import ValidationService

intent_service = IntentExtractionService()
design_service = SystemDesignService()
schema_service = SchemaGenerationService()
validation_service = ValidationService()


def _build_all(prompt: str):
    """Run a prompt through Stages 1-3, returning (IntentIR, SystemDesign, DataSchema)."""
    ir = intent_service.extract(prompt)
    design = design_service.build(ir)
    schema = schema_service.generate(ir, design)
    return ir, design, schema


def test_crm_pipeline_validates_cleanly() -> None:
    """A correctly generated CRM pipeline should produce zero findings and a 'proceed' decision."""
    ir, design, schema = _build_all("Build a CRM where users can log in and manage contacts.")

    report = validation_service.validate(ir, design, schema)

    assert report.findings == []
    assert report.status == "passed"
    assert report.pipeline_decision == "proceed"
    assert report.confidence == min(ir.confidence, design.confidence, schema.confidence)
    assert report.source_intent_id == ir.intent_id
    assert report.source_design_id == design.design_id
    assert report.source_schema_id == schema.schema_id


def test_todo_pipeline_validates_cleanly() -> None:
    """A correctly generated to-do pipeline (with an ownership relationship) should validate cleanly."""
    prompt = (
        "I want a simple app where users can sign up, log in, and manage a to-do list. "
        "Only logged-in users should see their own todos."
    )
    ir, design, schema = _build_all(prompt)

    report = validation_service.validate(ir, design, schema)

    assert report.findings == []
    assert report.status == "passed"
    assert report.consistency_summary.relationships_checked == 1
    assert report.consistency_summary.acknowledged_gaps == 0


def test_healthcare_pipeline_validates_cleanly_with_propagated_risks() -> None:
    """A healthcare pipeline whose high-severity risks were correctly propagated should validate cleanly."""
    prompt = (
        "Build a healthcare clinic system to manage patients, doctors, and appointments. "
        "This system must comply with HIPAA regulations."
    )
    ir, design, schema = _build_all(prompt)

    report = validation_service.validate(ir, design, schema)

    assert report.findings == []
    assert report.status == "passed"


def test_rejected_upstream_artifacts_cascade_to_halt() -> None:
    """If any upstream artifact is not 'complete', validation must halt regardless of other findings."""
    ir, design, schema = _build_all("")
    assert design.status == "rejected"
    assert schema.status == "rejected"

    report = validation_service.validate(ir, design, schema)

    assert report.pipeline_decision == "halt"
    assert report.status == "failed"
    assert any(f.category == "cross_stage_inconsistency" and f.severity == "critical" for f in report.findings)


def test_missing_schema_entity_is_flagged_as_critical_missing_entity() -> None:
    """Removing an entity from DataSchema (simulating a Stage 3 regression) must be caught, not silently passed."""
    ir, design, schema = _build_all("Build a CRM where users can log in and manage contacts.")
    broken_schema = schema.model_copy(deep=True)
    broken_schema.entities = [e for e in broken_schema.entities if e.name != "contact"]

    report = validation_service.validate(ir, design, broken_schema)

    assert report.pipeline_decision == "halt"
    assert any(
        f.category == "missing_entity" and f.severity == "critical" and "Contact" in f.message
        for f in report.findings
    )


def test_duplicate_module_names_are_flagged() -> None:
    """Two SystemDesign modules sharing the same name must be flagged as a duplicate_definition."""
    ir, design, schema = _build_all("Build a CRM where users can log in and manage contacts.")
    broken_design = design.model_copy(deep=True)
    broken_design.modules[1].name = broken_design.modules[0].name

    report = validation_service.validate(ir, broken_design, schema)

    assert any(f.category == "duplicate_definition" and f.severity == "critical" for f in report.findings)
    assert report.pipeline_decision == "halt"


def test_naming_drift_is_flagged_as_warning_not_blocking() -> None:
    """A SchemaEntity whose name drifts from the snake_case convention should warn but not block the pipeline.

    Uses the e-commerce prompt because it has no IR relationships and no high-severity design risks
    touching 'Payment', so renaming that one entity cannot also break a relationship or constraint
    reference (which would otherwise mask this as an invalid_reference finding instead).
    """
    prompt = (
        "Build an e-commerce store. Customers can manage orders and payments. "
        "Payment must be confirmed before an order is created."
    )
    ir, design, schema = _build_all(prompt)
    assert schema.relationships == []
    assert schema.constraints == []

    broken_schema = schema.model_copy(deep=True)
    payment_entity = next(e for e in broken_schema.entities if e.name == "payment")
    payment_entity.name = "Payments"

    report = validation_service.validate(ir, design, broken_schema)

    assert any(f.category == "naming_conflict" and f.severity == "warning" for f in report.findings)
    assert report.pipeline_decision == "proceed_with_warnings"
    assert report.status == "passed_with_warnings"


def test_invalid_capability_module_reference_is_flagged() -> None:
    """A Capability pointing at a module name that doesn't exist must be flagged as invalid_reference."""
    ir, design, schema = _build_all("Build a CRM where users can log in and manage contacts.")
    broken_design = design.model_copy(deep=True)
    broken_design.capabilities[0].module = "Nonexistent Module"

    report = validation_service.validate(ir, broken_design, schema)

    assert any(f.category == "invalid_reference" and f.severity == "critical" for f in report.findings)
    assert report.pipeline_decision == "halt"


def test_unpropagated_high_severity_risk_is_flagged() -> None:
    """A SystemDesign that drops a high-severity IntentIR risk_flag entirely must be flagged."""
    ir, design, schema = _build_all(
        "Build a healthcare clinic system to manage patients, doctors, and appointments. "
        "This system must comply with HIPAA regulations."
    )
    broken_design = design.model_copy(deep=True)
    broken_design.design_risks = [r for r in broken_design.design_risks if r.category != "medical_data"]

    report = validation_service.validate(ir, broken_design, schema)

    assert any(
        f.category == "risk_propagation_failure" and "medical_data" in f.message
        for f in report.findings
    )
    assert report.pipeline_decision == "halt"


def test_orphan_relationship_without_acknowledgement_is_flagged() -> None:
    """A relationship missing from DataSchema with no matching schema_ambiguity must be flagged, not assumed safe."""
    ir, design, schema = _build_all(
        "I want a simple app where users can sign up, log in, and manage a to-do list. "
        "Only logged-in users should see their own todos."
    )
    broken_schema = schema.model_copy(deep=True)
    broken_schema.relationships = []

    report = validation_service.validate(ir, design, broken_schema)

    assert any(f.category == "orphan_relationship" and f.severity == "error" for f in report.findings)
    assert report.pipeline_decision == "halt"


def test_missing_foreign_key_on_one_to_many_relationship_is_flagged() -> None:
    """A one_to_many SchemaRelationship with no foreign_key_field must be flagged as missing_required_field."""
    ir, design, schema = _build_all(
        "I want a simple app where users can sign up, log in, and manage a to-do list. "
        "Only logged-in users should see their own todos."
    )
    broken_schema = schema.model_copy(deep=True)
    broken_schema.relationships[0].foreign_key_field = None

    report = validation_service.validate(ir, design, broken_schema)

    assert any(
        f.category == "missing_required_field" and f.severity == "error" and "foreign_key_field" in f.related_field
        for f in report.findings
    )
    assert report.pipeline_decision == "halt"


def test_broken_intent_traceability_is_flagged() -> None:
    """A SystemDesign whose source_intent_id no longer matches the IntentIR must be flagged."""
    ir, design, schema = _build_all("Build a CRM where users can log in and manage contacts.")
    broken_design = design.model_copy(deep=True)
    broken_design.source_intent_id = "some-other-intent-id"

    report = validation_service.validate(ir, broken_design, schema)

    assert any(f.category == "broken_traceability" and "source_intent_id" in f.message for f in report.findings)
    assert report.pipeline_decision == "halt"
