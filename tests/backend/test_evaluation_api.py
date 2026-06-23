"""API-level test for the POST /evaluate endpoint."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_evaluate_endpoint_returns_benchmark_result() -> None:
    """Posting a small batch of cases should return a 200 BenchmarkResult with the new required fields."""
    response = client.post(
        "/evaluate",
        json={
            "dataset_name": "api-smoke-test",
            "cases": [
                {
                    "case_id": "crm_001",
                    "prompt": "Build a CRM where users can log in and manage contacts.",
                    "category": "crm",
                },
                {
                    "case_id": "vague_001",
                    "prompt": "Build me something cool.",
                    "category": "ambiguous",
                    "expectation": {"expect_halt": True},
                },
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["dataset_name"] == "api-smoke-test"
    assert body["dataset_size"] == 2
    assert "compiler_version" in body
    assert body["dataset_categories"] == {"crm": 1, "ambiguous": 1}
    assert body["status"] == "complete"
    assert "case_results" not in body  # the aggregate must never carry a per-case list


def test_evaluate_endpoint_with_empty_dataset_returns_zeroed_result() -> None:
    """An empty case list should return a well-formed, zeroed-out BenchmarkResult, not an error."""
    response = client.post("/evaluate", json={"dataset_name": "empty", "cases": []})

    assert response.status_code == 200
    body = response.json()
    assert body["dataset_size"] == 0
    assert body["success_rate"] == 0.0
    assert body["status"] == "complete"
