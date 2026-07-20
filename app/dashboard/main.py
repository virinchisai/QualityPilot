"""Streamlit operator dashboard for the local QualityPilot API."""

import json
import os

import httpx
import pandas as pd
import streamlit as st

API = os.getenv("QUALITYPILOT_API_URL", "http://localhost:8001")
EXECUTION_TOKEN = os.getenv("QUALITYPILOT_EXECUTION_TOKEN", "local-execution-only")
st.set_page_config(page_title="QualityPilot", page_icon="🧭", layout="wide")
st.title("QualityPilot TestOps")
st.caption("Deterministic, local-first requirement-to-evidence workflow")


def api_get(path: str):
    response = httpx.get(f"{API}{path}", timeout=10)
    response.raise_for_status()
    return response.json()


def api_post(path: str, payload: dict, timeout: float = 30):
    response = httpx.post(
        f"{API}{path}",
        json=payload,
        headers={"X-QualityPilot-Execution-Token": EXECUTION_TOKEN},
        timeout=timeout,
    )
    response.raise_for_status()
    return response


def split_csv_values(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


(
    tab_overview,
    tab_generate,
    tab_traceability,
    tab_demo,
    tab_flaky,
    tab_release,
    tab_ai,
) = st.tabs(
    [
        "Overview",
        "Requirement Lab",
        "Traceability",
        "Demo Console",
        "Flaky Tests",
        "Release Gate",
        "AI Quality",
    ]
)
with tab_overview:
    try:
        rows = api_get("/api/executions")
        total = len(rows)
        passed = sum(r["status"] == "passed" for r in rows)
        failed = sum(r["status"] == "failed" for r in rows)
        skipped = sum(r["status"] == "skipped" for r in rows)
        average = sum(r["duration_seconds"] for r in rows) / max(1, total)
        columns = st.columns(6)
        for column, label, value in zip(
            columns,
            ["Total", "Passed", "Failed", "Skipped", "Pass rate", "Avg duration"],
            [total, passed, failed, skipped, f"{passed / max(1, total):.1%}", f"{average:.2f}s"],
            strict=True,
        ):
            column.metric(label, value)
        if rows:
            frame = pd.DataFrame(rows)
            st.subheader("Execution history")
            st.dataframe(frame, width="stretch")
            st.subheader("Failure categories")
            st.bar_chart(frame[frame.status == "failed"].groupby("failure_signature").size())
        else:
            st.info("No executions recorded yet. Use the API or test reporter to add one.")
        defects = api_get("/api/defects")
        st.subheader("Recent defects")
        if defects:
            st.dataframe(pd.DataFrame(defects), width="stretch")
        else:
            st.caption("No defect reports generated yet.")
        st.subheader("Controlled local execution")
        st.caption("Runs only commands defined in the server-side suite allow-list.")
        run_api, run_identity = st.columns(2)
        if run_api.button("Run API suite", width="stretch"):
            with st.spinner("Running pytest API suite…"):
                result = api_post("/api/suites/api/run", {}, timeout=180).json()
            st.success(f"API suite {result['status']} in {result['duration_seconds']:.2f}s")
            st.code(result["output"][-3000:])
        if run_identity.button("Run identity suite", width="stretch"):
            with st.spinner("Running identity and security suite…"):
                result = api_post("/api/suites/identity/run", {}, timeout=180).json()
            st.success(f"Identity suite {result['status']} in {result['duration_seconds']:.2f}s")
            st.code(result["output"][-3000:])
    except Exception as exc:
        st.error(f"QualityPilot API unavailable: {exc}")

with tab_generate:
    sample = """requirements:
  - id: AUTH-001
    title: User login
    description: A registered user can sign in.
    acceptance_criteria:
      - Valid credentials return access and refresh tokens.
      - Invalid credentials return 401.
"""
    source_format = st.selectbox(
        "Input format", ["yaml", "markdown", "json", "text", "gherkin", "openapi"]
    )
    upload = st.file_uploader(
        "Upload a requirement",
        type=["yaml", "yml", "json", "md", "txt", "feature"],
    )
    initial_content = upload.getvalue().decode("utf-8") if upload else sample
    content = st.text_area("Or paste a requirement", initial_content, height=220)
    if st.button("Generate validated tests", type="primary"):
        try:
            response = api_post(
                "/api/requirements/generate",
                {"content": content, "source_format": source_format},
                timeout=20,
            )
            st.session_state["generation_results"] = response.json()
            st.session_state["generation_input"] = {
                "content": content,
                "source_format": source_format,
            }
        except httpx.HTTPError as exc:
            st.error(str(exc))
    for result in st.session_state.get("generation_results", []):
        st.subheader(result["requirement"]["title"])
        st.dataframe(pd.DataFrame(result["test_cases"]), width="stretch")
        st.code(result["gherkin"], language="gherkin")
        download_json, download_rally_json, download_rally_csv = st.columns(3)
        download_json.download_button(
            "Download QualityPilot JSON",
            json.dumps(result, indent=2),
            file_name=f"{result['requirement']['id']}.json",
        )
        export_input = st.session_state.get("generation_input")
        if export_input:
            rally_json = api_post(
                "/api/requirements/export/rally?export_format=json", export_input
            ).text
            rally_csv = api_post(
                "/api/requirements/export/rally?export_format=csv", export_input
            ).text
            download_rally_json.download_button(
                "Download Rally JSON",
                rally_json,
                file_name=f"{result['requirement']['id']}-rally.json",
                mime="application/json",
            )
            download_rally_csv.download_button(
                "Download Rally CSV",
                rally_csv,
                file_name=f"{result['requirement']['id']}-rally.csv",
                mime="text/csv",
            )

with tab_traceability:
    st.subheader("Requirements traceability matrix")
    st.caption("Generated from committed sample requirements, test cases, and latest history.")
    matrix = api_get("/api/traceability")
    st.dataframe(pd.DataFrame(matrix), width="stretch", hide_index=True)

with tab_demo:
    st.subheader("Controlled defect demonstration")
    st.warning(
        "This creates deterministic demo evidence without weakening the running service. "
        "Environment fault flags remain disabled."
    )
    fault = st.selectbox(
        "Failure to demonstrate",
        [
            "Refresh token replay accepted",
            "Standard user received admin access",
            "Login API returned an unexpected status",
            "Playwright locator timed out",
        ],
    )
    fault_messages = {
        "Refresh token replay accepted": "expected 401 invalid token, received status code 200",
        "Standard user received admin access": "expected 403 forbidden, received status code 200",
        "Login API returned an unexpected status": "expected status code 200 got 500",
        "Playwright locator timed out": "locator selector timed out waiting for element",
    }
    if st.button("Analyze and generate defect", type="primary"):
        payload = {
            "failure": {
                "test_name": fault,
                "error_message": fault_messages[fault],
                "environment": {"name": "controlled-dashboard-demo"},
                "previous_statuses": ["passed", "failed", "passed", "failed"]
                if "locator" in fault.lower()
                else [],
            },
            "related_test_case": "DEMO-" + fault.upper().replace(" ", "-")[:40],
            "commit_sha": "local-demo",
        }
        st.session_state["demo_defect"] = api_post("/api/defects", payload).json()
    if defect := st.session_state.get("demo_defect"):
        report = defect["report"]
        st.success(f"{report['defect_id']} classified as {report['labels'][0]} and persisted")
        st.markdown(defect["markdown"])
        markdown_download, json_download = st.columns(2)
        markdown_download.download_button(
            "Download Markdown report",
            defect["markdown"],
            file_name=f"{report['defect_id']}.md",
            mime="text/markdown",
        )
        json_download.download_button(
            "Download JSON report",
            json.dumps(report, indent=2),
            file_name=f"{report['defect_id']}.json",
            mime="application/json",
        )

with tab_flaky:
    test_id = st.text_input("Test ID", "TC-AUTH-001-001")
    if st.button("Analyze history"):
        result = api_get(f"/api/flaky/{test_id}")
        st.metric("Flakiness score", result["flakiness_score"])
        st.write(result)

with tab_release:
    st.subheader("Release-level quality gates")
    st.caption("Evaluate a release using configurable, deterministic blocking rules.")
    total_tests = st.number_input("Total tests", min_value=1, value=39)
    passed_tests = st.number_input(
        "Passed tests", min_value=0, max_value=int(total_tests), value=39
    )
    threshold = st.slider("Minimum pass rate", 0.0, 1.0, 0.95, 0.01)
    smoke_failures = st.text_input("Smoke failures (comma separated)")
    security_failures = st.text_input("Critical security failures (comma separated)")
    flaky_tests = st.text_input("High-confidence flaky tests (comma separated)")
    critical_defects = st.text_input("Critical open defects (comma separated)")
    if st.button("Evaluate release"):
        payload = {
            "evidence": {
                "smoke_failures": split_csv_values(smoke_failures),
                "critical_security_failures": split_csv_values(security_failures),
                "passed_tests": passed_tests,
                "total_tests": total_tests,
                "high_confidence_flaky_tests": split_csv_values(flaky_tests),
                "critical_open_defects": split_csv_values(critical_defects),
            },
            "config": {"minimum_pass_rate": threshold},
        }
        decision = api_post("/api/release-gates/evaluate", payload).json()
        if decision["release_decision"] == "approved":
            st.success(f"Release approved at {decision['pass_rate']:.1%} pass rate")
        else:
            st.error("Release blocked")
            for reason in decision["reasons"]:
                st.write(f"- {reason}")
        st.json(decision)

with tab_ai:
    prompt = st.text_input("Agent prompt", "How does refresh rotation work?")
    if st.button("Evaluate agent"):
        agent = httpx.post(f"{API}/api/ai/agent", json={"prompt": prompt}, timeout=10).json()
        evaluation = httpx.post(
            f"{API}/api/ai/evaluate", json={"prompt": prompt, "response": agent}, timeout=10
        ).json()
        st.json({"response": agent, "evaluation": evaluation})
