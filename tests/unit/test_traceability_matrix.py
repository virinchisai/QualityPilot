from datetime import datetime

from qualitypilot.database import TestExecution as ExecutionRecord
from qualitypilot.generators.deterministic import DeterministicTestGenerator
from qualitypilot.models.test_case import Requirement
from qualitypilot.traceability.matrix import build_traceability_matrix


def test_matrix_links_requirement_cases_surfaces_and_last_result():
    requirement = Requirement(
        id="AUTH-001", title="User login", description="A registered user signs in"
    )
    cases = DeterministicTestGenerator().generate(requirement).test_cases
    execution = ExecutionRecord(
        execution_id="run-1",
        test_id=cases[0].test_id,
        status="passed",
        duration_seconds=1.2,
        timestamp=datetime(2026, 1, 1),
    )
    row = build_traceability_matrix([requirement], cases, [execution])[0]
    assert row["requirement_id"] == "AUTH-001"
    assert row["test_cases"] == len(cases)
    assert row["api"] and row["ui"] and row["bdd"] and row["security"]
    assert row["last_result"] == "passed"
