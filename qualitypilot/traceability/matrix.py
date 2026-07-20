"""Requirement-to-test traceability matrix generation."""

from collections import defaultdict
from collections.abc import Iterable

from qualitypilot.database import TestExecution
from qualitypilot.models.test_case import Requirement, TestCase, TestType


def build_traceability_matrix(
    requirements: Iterable[Requirement],
    test_cases: Iterable[TestCase],
    executions: Iterable[TestExecution] = (),
) -> list[dict]:
    cases_by_requirement: dict[str, list[TestCase]] = defaultdict(list)
    for test_case in test_cases:
        cases_by_requirement[test_case.requirement_id].append(test_case)

    latest_by_test: dict[str, TestExecution] = {}
    for execution in sorted(executions, key=lambda item: item.timestamp):
        latest_by_test[execution.test_id] = execution

    rows = []
    for requirement in requirements:
        cases = cases_by_requirement[requirement.id]
        latest = [latest_by_test[case.test_id] for case in cases if case.test_id in latest_by_test]
        last_result = max(latest, key=lambda item: item.timestamp).status if latest else "not_run"
        types = {case.test_type for case in cases}
        rows.append(
            {
                "requirement_id": requirement.id,
                "requirement": requirement.title,
                "test_cases": len(cases),
                "api": TestType.API in types or any(case.related_endpoint for case in cases),
                "ui": TestType.UI in types or any(case.related_ui_page for case in cases),
                "bdd": bool(cases),
                "security": TestType.SECURITY in types,
                "automated": sum(case.automation_candidate for case in cases),
                "last_result": last_result,
                "test_ids": [case.test_id for case in cases],
            }
        )
    return rows
