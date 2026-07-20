from datetime import datetime, timedelta

from qualitypilot.database import TestExecution as ExecutionRecord
from qualitypilot.flaky_detection.detector import FlakyDetector, failure_signature


def rows(statuses, retries=None, signature="timeout waiting 17 seconds"):
    retries = retries or [0] * len(statuses)
    return [
        ExecutionRecord(
            execution_id=str(i),
            test_id="T1",
            status=status,
            duration_seconds=1,
            retry_count=retries[i],
            failure_signature=signature,
            timestamp=datetime(2025, 1, 1) + timedelta(minutes=i),
        )
        for i, status in enumerate(statuses)
    ]


def test_transition_score_marks_alternating_history():
    result = FlakyDetector().analyze("T1", rows(["passed", "failed", "passed", "failed"]))
    assert result.is_likely_flaky and result.flakiness_score >= 0.8
    assert result.probable_cause == "timing instability"


def test_stable_history_not_flaky():
    result = FlakyDetector().analyze("T1", rows(["passed"] * 6))
    assert not result.is_likely_flaky and result.flakiness_score == 0


def test_signature_removes_variable_numbers():
    assert failure_signature("Timeout after 123 ms") == "timeout after # ms"
