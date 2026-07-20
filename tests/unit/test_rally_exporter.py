import csv
import io
import json

from qualitypilot.exporters.rally import RallyTestCaseExporter
from qualitypilot.generators.deterministic import DeterministicTestGenerator
from qualitypilot.models.test_case import Requirement


def generated_cases():
    requirement = Requirement(
        id="AUTH-001",
        title="User login",
        description="A registered user signs in with valid credentials.",
    )
    return DeterministicTestGenerator().generate(requirement).test_cases


def test_rally_json_contains_enterprise_test_case_fields():
    records = json.loads(RallyTestCaseExporter().to_json(generated_cases()))
    assert records[0]["WorkProduct"] == "AUTH-001"
    assert records[0]["Method"] == "Automated"
    assert records[0]["Steps"][0]["StepIndex"] == 1
    assert records[0]["ExpectedResult"]


def test_rally_csv_round_trips_steps_as_json():
    rows = list(csv.DictReader(io.StringIO(RallyTestCaseExporter().to_csv(generated_cases()))))
    assert rows[0]["FormattedID"].startswith("TC-AUTH-001")
    assert json.loads(rows[0]["Steps"])[0]["Input"]
