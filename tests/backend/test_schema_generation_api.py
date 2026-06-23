"""API-level test for the POST /schema-generation endpoint."""
from fastapi.testclient import TestClient

from app.main import app
from app.services.intent_extraction import IntentExtractionService
from app.services.system_design import SystemDesignService

client = TestClient(app)
intent_service = IntentExtractionService()
design_service = SystemDesignService()


def test_schema_generation_endpoint_returns_data_schema() -> None:
    """Posting a valid IntentIR + SystemDesign JSON body should return a 200 DataSchema response."""
    ir = intent_service.extract("Build a CRM where users can log in and manage contacts.")
    design = design_service.build(ir)

    response = client.post(
        "/schema-generation",
        json={"intent_ir": ir.model_dump(), "system_design": design.model_dump()},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source_intent_id"] == ir.intent_id
    assert body["source_design_id"] == design.design_id
    assert body["status"] == "complete"
    assert any(entity["name"] == "contact" for entity in body["entities"])
