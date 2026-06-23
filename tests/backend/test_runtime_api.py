"""API-level test for the POST /compile endpoint."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_compile_endpoint_returns_compilation_result() -> None:
    """Posting a prompt should return a 200 CompilationResult covering all four stages."""
    response = client.post(
        "/compile", json={"prompt": "Build a CRM where users can log in and manage contacts."}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["overall_status"] == "succeeded"
    assert body["final_decision"] == "proceed"
    assert [s["stage_name"] for s in body["stage_summaries"]] == [
        "intent_extraction",
        "system_design",
        "schema_generation",
        "validation",
    ]
    assert body["intent_ir"] is not None
    assert body["validation_report"]["findings"] == []


def test_compile_endpoint_handles_empty_prompt_without_error() -> None:
    """Posting an empty prompt should still return 200 with a well-formed, halted CompilationResult."""
    response = client.post("/compile", json={"prompt": ""})

    assert response.status_code == 200
    body = response.json()
    assert body["overall_status"] == "halted"
    assert body["final_decision"] == "halt"
    assert body["error"] is None
