import json

import pytest

from qualitypilot.generators.deterministic import DeterministicTestGenerator
from qualitypilot.models.test_case import TestCase as CaseModel
from qualitypilot.requirements.parser import LocalRequirementAdapter


@pytest.mark.parametrize(
    ("content", "fmt", "title"),
    [
        ("A user can log in", "text", "A user can log in"),
        ("# Login\n\n- Valid credentials work", "markdown", "Login"),
        (json.dumps({"id": "R1", "title": "Login", "description": "Sign in"}), "json", "Login"),
        ("id: R2\ntitle: Logout\ndescription: End a session", "yaml", "Logout"),
        ("Feature: Refresh token\n  Scenario: Rotate token", "gherkin", "Refresh token"),
        (
            """openapi: 3.1.0
paths:
  /health:
    get:
      summary: Health
      responses:
        '200': {}
""",
            "openapi",
            "Health",
        ),
    ],
)
def test_supported_requirement_formats(content, fmt, title):
    assert LocalRequirementAdapter().ingest(content, fmt)[0].title == title


def test_gherkin_parser_handles_long_untrusted_whitespace_without_regex_backtracking():
    content = "Feature:" + (" " * 100_000) + "Safe parsing\n  Scenario: remains responsive"

    requirement = LocalRequirementAdapter().ingest(content, "gherkin")[0]

    assert requirement.title == "Safe parsing"
    assert requirement.acceptance_criteria == ["remains responsive"]


def test_generator_validates_complete_cases_and_traceability():
    requirement = LocalRequirementAdapter().ingest("User login", "text")[0]
    result = DeterministicTestGenerator().generate(requirement)
    assert len(result.test_cases) == 4
    assert all(CaseModel.model_validate(case.model_dump()) for case in result.test_cases)
    assert all(case.requirement_id == requirement.id for case in result.test_cases)
    assert requirement.id.replace("-", "_") in result.gherkin


def test_unknown_format_is_rejected():
    with pytest.raises(ValueError, match="unsupported"):
        LocalRequirementAdapter().ingest("x", "docx")
