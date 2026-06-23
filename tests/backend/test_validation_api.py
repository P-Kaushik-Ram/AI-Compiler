"""API-level test for the POST /validate endpoint."""
from fastapi.testclient import TestClient

from app.main import app
from app.services.intent_extraction import IntentExtractionService
from app.services.schema_generation import SchemaGenerationService
from app.services.system_design import SystemDesignService

client = TestClient(app)
intent_service = IntentExtractionService()
design_service = SystemDesignService()
schema_service = SchemaGenerationService()


def test_validate_endpoint_returns_validation_report() -> None:
    """Posting a valid IntentIR + SystemDesign + DataSchema body should return a 200 ValidationReport."""
    ir = intent_service.extract("Build a CRM where users can log in and manage contacts.")
    design = design_service.build(ir)
    schema = schema_service.generate(ir, design)

    response = client.post(
        "/validate",
        json={
            "intent_ir": ir.model_dump(),
            "system_design": design.model_dump(),
            "data_schema": schema.model_dump(),
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source_intent_id"] == ir.intent_id
    assert body["source_design_id"] == design.design_id
    assert body["source_schema_id"] == schema.schema_id
    assert body["status"] == "passed"
    assert body["pipeline_decision"] == "proceed"
    assert body["findings"] == []
