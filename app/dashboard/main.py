"""Streamlit operator dashboard for the local QualityPilot API."""

import json
import os

import httpx
import pandas as pd
import streamlit as st

API = os.getenv("QUALITYPILOT_API_URL", "http://localhost:8001")
st.set_page_config(page_title="QualityPilot", page_icon="🧭", layout="wide")
st.title("QualityPilot TestOps")
st.caption("Deterministic, local-first requirement-to-evidence workflow")


def api_get(path: str):
    response = httpx.get(f"{API}{path}", timeout=10)
    response.raise_for_status()
    return response.json()


tab_overview, tab_generate, tab_flaky, tab_ai = st.tabs(
    ["Overview", "Requirement Lab", "Flaky Tests", "AI Quality"]
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
            st.dataframe(frame, use_container_width=True)
            st.subheader("Failure categories")
            st.bar_chart(frame[frame.status == "failed"].groupby("failure_signature").size())
        else:
            st.info("No executions recorded yet. Use the API or test reporter to add one.")
        defects = api_get("/api/defects")
        st.subheader("Recent defects")
        if defects:
            st.dataframe(pd.DataFrame(defects), use_container_width=True)
        else:
            st.caption("No defect reports generated yet.")
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
    content = st.text_area("Requirement", sample, height=220)
    if st.button("Generate validated tests", type="primary"):
        response = httpx.post(
            f"{API}/api/requirements/generate",
            json={"content": content, "source_format": source_format},
            timeout=20,
        )
        if response.is_success:
            results = response.json()
            for result in results:
                st.subheader(result["requirement"]["title"])
                st.dataframe(pd.DataFrame(result["test_cases"]), use_container_width=True)
                st.code(result["gherkin"], language="gherkin")
                st.download_button(
                    "Download JSON",
                    json.dumps(result, indent=2),
                    file_name=f"{result['requirement']['id']}.json",
                )
        else:
            st.error(response.text)

with tab_flaky:
    test_id = st.text_input("Test ID", "TC-AUTH-001-001")
    if st.button("Analyze history"):
        result = api_get(f"/api/flaky/{test_id}")
        st.metric("Flakiness score", result["flakiness_score"])
        st.write(result)

with tab_ai:
    prompt = st.text_input("Agent prompt", "How does refresh rotation work?")
    if st.button("Evaluate agent"):
        agent = httpx.post(f"{API}/api/ai/agent", json={"prompt": prompt}, timeout=10).json()
        evaluation = httpx.post(
            f"{API}/api/ai/evaluate", json={"prompt": prompt, "response": agent}, timeout=10
        ).json()
        st.json({"response": agent, "evaluation": evaluation})
