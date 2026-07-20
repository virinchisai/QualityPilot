from fastapi.testclient import TestClient

from app.backend.main import app


def test_generate_analyze_and_ai_endpoints():
    with TestClient(app) as client:
        generated = client.post(
            "/api/requirements/generate", json={"source_format": "text", "content": "User login"}
        )
        assert generated.status_code == 200 and generated.json()[0]["test_cases"]
        analysis = client.post(
            "/api/failures/analyze", json={"test_name": "auth", "error_message": "403 forbidden"}
        )
        assert analysis.json()["failure_type"] == "authorization_failure"
        agent = client.post("/api/ai/agent", json={"prompt": "Explain RBAC"}).json()
        assert agent["citations"] == ["kb:rbac"]


def test_execution_history_and_flaky_result():
    with TestClient(app) as client:
        for status in ["passed", "failed", "passed", "failed"]:
            assert (
                client.post(
                    "/api/executions",
                    json={
                        "test_id": "T-FLAKY",
                        "status": status,
                        "error_message": "timeout waiting 5 seconds",
                    },
                ).status_code
                == 201
            )
        result = client.get("/api/flaky/T-FLAKY").json()
        assert result["is_likely_flaky"]
