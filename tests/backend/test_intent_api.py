"""API-level test for the POST /intent/extract endpoint."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_extract_endpoint_returns_intent_ir() -> None:
    """The endpoint should return a 200 response shaped like an IntentIR for a valid prompt."""
    response = client.post("/intent/extract", json={"prompt": "Build a CRM with login and contacts."})

    assert response.status_code == 200
    body = response.json()
    assert body["domain"] == "crm"
    assert body["status"] == "complete"
    assert any(entity["name"] == "Contact" for entity in body["entities"])
