"""History persistence and transition-based flakiness signals."""

import re
import uuid

from sqlalchemy.orm import Session

from qualitypilot.database import TestExecution
from qualitypilot.models.analysis import FlakyResult
from qualitypilot.observability.metrics import FLAKY_TESTS, TEST_EXECUTIONS


def failure_signature(message: str | None) -> str | None:
    if not message:
        return None
    normalized = re.sub(r"\b\d+(?:\.\d+)?\b", "#", message.lower())
    return re.sub(r"\s+", " ", normalized).strip()[:255]


def record_execution(db: Session, **values) -> TestExecution:
    execution = TestExecution(execution_id=values.pop("execution_id", str(uuid.uuid4())), **values)
    db.add(execution)
    db.commit()
    db.refresh(execution)
    TEST_EXECUTIONS.labels(execution.status).inc()
    return execution


class FlakyDetector:
    def analyze(self, test_id: str, executions: list[TestExecution]) -> FlakyResult:
        ordered = sorted(executions, key=lambda row: row.timestamp)[-20:]
        history = [row.status.lower() for row in ordered]
        transitions = sum(left != right for left, right in zip(history, history[1:], strict=False))
        transition_ratio = transitions / max(1, len(history) - 1)
        retries = sum(row.retry_count > 0 for row in ordered) / max(1, len(ordered))
        score = round(min(1, transition_ratio * 0.8 + retries * 0.2), 3)
        cause, action = self._cause(ordered)
        likely = len(history) >= 4 and "passed" in history and "failed" in history and score >= 0.45
        if likely:
            FLAKY_TESTS.inc()
        return FlakyResult(
            test_id=test_id,
            flakiness_score=score,
            history=history,
            probable_cause=cause,
            suggested_stabilization=action,
            is_likely_flaky=likely,
        )

    @staticmethod
    def _cause(rows):
        signatures = " ".join(row.failure_signature or "" for row in rows)
        if any(word in signatures for word in ("locator", "selector", "element")):
            return "weak locator", "Use role/label locators and a stable UI contract"
        if any(word in signatures for word in ("timeout", "timing", "wait")):
            return "timing instability", "Wait on observable state and remove fixed sleeps"
        if any(word in signatures for word in ("duplicate", "unique", "fixture")):
            return "shared test data", "Generate isolated data and clean up transactionally"
        if any(row.retry_count for row in rows):
            return "retry masking", "Re-run without retries and compare trace signatures"
        return (
            "race, ordering, network, or environment instability",
            "Compare traces, ordering, browser, environment, and dependency latency",
        )
