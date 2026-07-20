from qualitypilot.analysis.failure_analyzer import DeterministicFailureAnalyzer
from qualitypilot.defect_reporting.reporter import build_defect, to_jira_payload, to_markdown
from qualitypilot.models.analysis import DefectReport, FailureInput


def test_all_report_formats_round_trip():
    failure = FailureInput(
        test_name="login rejects valid user",
        error_message="expected status code 200 got 500",
        environment={"browser": "chromium"},
    )
    analysis = DeterministicFailureAnalyzer().analyze(failure)
    report = build_defect(failure, analysis, "TC-AUTH-001")
    assert DefectReport.model_validate_json(report.model_dump_json()).defect_id == "QP-TC-AUTH-001"
    assert "Steps to reproduce" in to_markdown(report)
    jira = to_jira_payload(report)
    assert jira["fields"]["issuetype"]["name"] == "Bug"
