"""API-level test for the POST /system-design endpoint."""
from fastapi.testclient import TestClient

from app.main import app
from app.services.intent_extraction import IntentExtractionService

client = TestClient(app)
intent_service = IntentExtractionService()


def test_system_design_endpoint_returns_system_design() -> None:
    """Posting a valid IntentIR JSON body should return a 200 SystemDesign response."""
    ir = intent_service.extract("Build a CRM where users can log in and manage contacts.")

    response = client.post("/system-design", json=ir.model_dump())

    assert response.status_code == 200
    body = response.json()
    assert body["source_intent_id"] == ir.intent_id
    assert body["status"] == "complete"
    assert any(module["name"] == "Authentication" for module in body["modules"])
