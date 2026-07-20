import pytest

from qualitypilot.analysis.failure_analyzer import DeterministicFailureAnalyzer
from qualitypilot.models.analysis import FailureInput, FailureType


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("received 401 invalid token", FailureType.AUTHENTICATION_FAILURE),
        ("403 forbidden for user", FailureType.AUTHORIZATION_FAILURE),
        ("connection refused to service", FailureType.ENVIRONMENT_ISSUE),
        ("locator resolved to zero elements", FailureType.TEST_DEFECT),
        ("expected status code 200", FailureType.APPLICATION_DEFECT),
    ],
)
def test_classification(message, expected):
    result = DeterministicFailureAnalyzer().analyze(
        FailureInput(test_name="example", error_message=message)
    )
    assert result.failure_type == expected
    assert result.evidence and 0 <= result.confidence <= 1


def test_alternating_history_is_flaky():
    result = DeterministicFailureAnalyzer().analyze(
        FailureInput(
            test_name="example", previous_statuses=["passed", "failed", "passed", "failed"]
        )
    )
    assert result.failure_type == FailureType.FLAKY_BEHAVIOR
    assert result.retry_recommended
