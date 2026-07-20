"""Defect report creation and serialization."""

import json
import re
from pathlib import Path

from qualitypilot.models.analysis import DefectReport, FailureAnalysis, FailureInput


def build_defect(
    failure: FailureInput, analysis: FailureAnalysis, related_test_case: str, commit: str = "local"
) -> DefectReport:
    safe_id = re.sub(r"[^A-Z0-9]+", "-", related_test_case.upper()).strip("-")
    return DefectReport(
        defect_id=f"QP-{safe_id}",
        title=f"[{analysis.affected_component}] {failure.test_name} failed",
        summary=analysis.probable_cause,
        severity="major",
        priority="high",
        component=analysis.affected_component,
        environment=failure.environment,
        build_commit=commit,
        preconditions=["The target environment is healthy"],
        steps_to_reproduce=[
            f"Run test {related_test_case}",
            "Observe the recorded failure and evidence",
        ],
        expected_result="The automated acceptance check passes",
        actual_result=failure.error_message or "Test failed",
        logs=failure.browser_console_logs,
        screenshot_references=[failure.screenshot_path] if failure.screenshot_path else [],
        trace_references=[failure.trace_path] if failure.trace_path else [],
        api_request_response={"request": failure.http_request, "response": failure.http_response}
        if failure.http_request or failure.http_response
        else None,
        suspected_cause=analysis.probable_cause,
        recommended_owner=analysis.recommended_owner,
        related_test_case=related_test_case,
        labels=[analysis.failure_type.value, "qualitypilot"],
    )


def to_markdown(report: DefectReport) -> str:
    steps = "\n".join(f"{i}. {step}" for i, step in enumerate(report.steps_to_reproduce, 1))
    return f"""# {report.defect_id}: {report.title}

**Severity:** {report.severity}  
**Priority:** {report.priority}  
**Component:** {report.component}  
**Build/commit:** {report.build_commit}  
**Related test:** {report.related_test_case}

## Summary

{report.summary}

## Steps to reproduce

{steps}

## Expected

{report.expected_result}

## Actual

{report.actual_result}

## Suspected cause and owner

{report.suspected_cause} — {report.recommended_owner}

Generated at {report.timestamp.isoformat()}.
"""


def to_jira_payload(report: DefectReport) -> dict:
    return {
        "fields": {
            "project": {"key": "QP"},
            "summary": report.title,
            "description": to_markdown(report),
            "issuetype": {"name": "Bug"},
            "priority": {"name": report.priority.title()},
            "labels": report.labels,
        }
    }


def write_reports(report: DefectReport, directory: Path) -> dict[str, str]:
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / f"{report.defect_id}.json"
    markdown_path = directory / f"{report.defect_id}.md"
    json_path.write_text(json.dumps(report.model_dump(mode="json"), indent=2), encoding="utf-8")
    markdown_path.write_text(to_markdown(report), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(markdown_path)}
