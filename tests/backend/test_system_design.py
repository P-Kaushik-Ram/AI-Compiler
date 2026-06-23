"""Unit tests for the deterministic SystemDesignService."""
from app.models.intent import Action, Attribute, Entity, IntentIR, RiskFlag, UserStory
from app.services.intent_extraction import IntentExtractionService
from app.services.system_design import SystemDesignService

intent_service = IntentExtractionService()
design_service = SystemDesignService()


def test_crm_ir_produces_authentication_and_contact_modules() -> None:
    """A CRM IntentIR should split into an isolated Authentication module plus Contact Management."""
    ir = intent_service.extract("Build a CRM where users can log in and manage contacts.")
    design = design_service.build(ir)

    assert design.status == "complete"
    assert design.source_intent_id == ir.intent_id
    module_names = {m.name for m in design.modules}
    assert "Authentication" in module_names
    assert "Contact Management" in module_names

    capability_names = {c.name for c in design.capabilities}
    assert "Account Access" in capability_names
    assert "Contact Management" in capability_names

    assert any(
        dep.from_module == "Contact Management" and dep.to_module == "Authentication" and dep.dependency_type == "data"
        for dep in design.module_dependencies
    )


def test_todo_ir_produces_owns_relationship_dependency() -> None:
    """A to-do IntentIR with ownership language should produce a data dependency on Authentication."""
    prompt = (
        "I want a simple app where users can sign up, log in, and manage a to-do list. "
        "Only logged-in users should see their own todos."
    )
    ir = intent_service.extract(prompt)
    design = design_service.build(ir)

    assert design.status == "complete"
    module_names = {m.name for m in design.modules}
    assert {"Authentication", "Todo Management"}.issubset(module_names)
    assert any(
        dep.from_module == "Todo Management" and dep.to_module == "Authentication"
        for dep in design.module_dependencies
    )
    assert any(actor.name == "User" and "Todo Management" in actor.accessible_capabilities for actor in design.actors)


def test_ecommerce_ir_isolates_payment_and_orders_workflow() -> None:
    """An e-commerce IntentIR with sequencing language should produce a Payment-before-Order workflow."""
    prompt = (
        "Build an e-commerce store. Customers can manage orders and payments. "
        "Payment must be confirmed before an order is created."
    )
    ir = intent_service.extract(prompt)
    design = design_service.build(ir)

    assert design.status == "complete"
    module_names = {m.name for m in design.modules}
    assert {"Customer Management", "Order Management", "Payment Management"}.issubset(module_names)

    payment_capability = next(c for c in design.capabilities if c.name == "Payment Management")
    order_capability = next(c for c in design.capabilities if c.name == "Order Management")
    assert payment_capability.risk_level == "medium"
    assert order_capability.risk_level == "medium"

    assert len(design.workflows) == 1
    workflow = design.workflows[0]
    assert [step.capability for step in workflow.steps] == ["Payment Management", "Order Management"]
    assert workflow.steps[1].depends_on == [workflow.steps[0].step_name]

    assert any(
        dep.dependency_type == "workflow"
        and dep.from_module == "Order Management"
        and dep.to_module == "Payment Management"
        for dep in design.module_dependencies
    )


def test_healthcare_ir_flags_high_severity_risks() -> None:
    """A healthcare IntentIR should isolate Patient data and propagate high-severity design risks."""
    prompt = (
        "Build a healthcare clinic system to manage patients, doctors, and appointments. "
        "This system must comply with HIPAA regulations."
    )
    ir = intent_service.extract(prompt)
    design = design_service.build(ir)

    assert design.status == "complete"
    module_names = {m.name for m in design.modules}
    assert {"Patient Management", "Doctor Management", "Appointment Management"}.issubset(module_names)

    risk_categories = {r.category for r in design.design_risks}
    assert {"medical_data", "compliance"}.issubset(risk_categories)

    medical_risk = next(r for r in design.design_risks if r.category == "medical_data")
    assert medical_risk.severity == "high"
    assert "Patient Management" in medical_risk.affected_modules
    assert "Doctor Management" in medical_risk.affected_modules

    compliance_risk = next(r for r in design.design_risks if r.category == "compliance")
    assert compliance_risk.affected_modules == ["Patient Management"]

    patient_capability = next(c for c in design.capabilities if c.name == "Patient Management")
    assert patient_capability.risk_level == "high"


def test_rejected_ir_produces_rejected_design() -> None:
    """An empty-prompt IntentIR (status='rejected') must produce a rejected SystemDesign, not a guessed one."""
    ir = intent_service.extract("")
    design = design_service.build(ir)

    assert design.status == "rejected"
    assert design.confidence == 0.0
    assert design.modules == []
    assert design.design_ambiguities[0].severity == "blocking"


def test_needs_clarification_ir_is_also_rejected_by_design() -> None:
    """An IntentIR that itself needs clarification must not be designed on top of."""
    ir = intent_service.extract("Build me something cool.")
    assert ir.status == "needs_clarification"

    design = design_service.build(ir)

    assert design.status == "rejected"
    assert design.modules == []


def test_high_severity_unmapped_risk_falls_back_to_all_modules() -> None:
    """A high/critical risk flag with no entity or PII mapping must attach to every module, not be dropped."""
    ir = IntentIR(
        intent_id="manual-001",
        version="1.0",
        domain="general",
        primary_intent="build_app",
        domain_summary="A manual test IR with a single non-sensitive entity.",
        entities=[
            Entity(
                name="Contact",
                description="A tracked contact",
                attributes=[Attribute(name="name", type_hint="string", is_optional=False)],
                confidence=0.9,
            )
        ],
        actions=[Action(name="create_contact", target_entity="Contact", description="Add a contact", confidence=0.9)],
        user_stories=[UserStory(actor="User", goal="create a contact", priority="must_have", related_action="create_contact")],
        risk_flags=[
            RiskFlag(
                category="legal",
                description="Manually injected legal risk with no clear entity mapping.",
                severity="critical",
            )
        ],
        confidence=0.9,
        status="complete",
        raw_prompt="manual test",
    )

    design = design_service.build(ir)

    legal_risk = next(r for r in design.design_risks if r.category == "legal")
    all_module_names = sorted(m.name for m in design.modules)
    assert legal_risk.affected_modules == all_module_names
    assert legal_risk.severity == "critical"
