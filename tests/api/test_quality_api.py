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


def test_defect_is_rendered_and_persisted():
    with TestClient(app) as client:
        response = client.post(
            "/api/defects",
            json={
                "failure": {
                    "test_name": "login",
                    "error_message": "expected status code 200 got 500",
                },
                "related_test_case": "TC-AUTH-DEFECT",
            },
        )
        assert response.status_code == 200
        assert response.json()["jira_payload"]["fields"]["issuetype"]["name"] == "Bug"
        stored = client.get("/api/defects").json()
        assert any(item["defect_id"] == "QP-TC-AUTH-DEFECT" for item in stored)


def test_rally_traceability_and_release_gate_endpoints():
    requirement = {
        "source_format": "yaml",
        "content": "id: AUTH-001\ntitle: User login\ndescription: A user signs in",
    }
    with TestClient(app) as client:
        rally = client.post("/api/requirements/export/rally?export_format=json", json=requirement)
        assert rally.status_code == 200
        assert rally.json()[0]["WorkProduct"] == "AUTH-001"

        matrix = client.get("/api/traceability")
        assert matrix.status_code == 200
        assert any(row["requirement_id"] == "AUTH-001" for row in matrix.json())

        gate = client.post(
            "/api/release-gates/evaluate",
            json={"evidence": {"passed_tests": 38, "total_tests": 39}},
        )
        assert gate.status_code == 200
        assert gate.json()["release_decision"] == "approved"


def test_suite_execution_requires_separate_token():
    with TestClient(app) as client:
        assert client.post("/api/suites/unit/run").status_code == 401
        suites = client.get("/api/suites").json()["suites"]
        assert {"unit", "api", "identity", "bdd", "playwright"} <= set(suites)
