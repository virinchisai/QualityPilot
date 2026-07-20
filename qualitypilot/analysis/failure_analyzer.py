"""Explainable failure classification rules."""

from qualitypilot.adapters.base import FailureAnalyzerAdapter
from qualitypilot.models.analysis import FailureAnalysis, FailureInput, FailureType
from qualitypilot.observability.metrics import FAILURE_CATEGORIES


class DeterministicFailureAnalyzer(FailureAnalyzerAdapter):
    RULES = [
        (
            ("401", "invalid token", "expired token", "unauthenticated"),
            FailureType.AUTHENTICATION_FAILURE,
            "identity",
            "security/backend",
            "Inspect token claims, clock, signature, expiry, and revocation state",
        ),
        (
            ("403", "forbidden", "admin role", "permission"),
            FailureType.AUTHORIZATION_FAILURE,
            "authorization",
            "security/backend",
            "Compare required role with server-side policy and token subject",
        ),
        (
            ("connection refused", "dns", "browser closed", "no space", "timeout connecting"),
            FailureType.ENVIRONMENT_ISSUE,
            "test environment",
            "platform",
            "Check service health, runner resources, network, and dependency readiness",
        ),
        (
            ("502", "503", "upstream", "dependency"),
            FailureType.DEPENDENCY_FAILURE,
            "external dependency",
            "service owner",
            "Check dependency health and isolate with a controlled stub",
        ),
        (
            ("locator", "strict mode", "element not found", "selector"),
            FailureType.TEST_DEFECT,
            "UI automation",
            "quality engineering",
            "Replace the locator with an accessible role or stable test contract",
        ),
        (
            ("unique constraint", "fixture", "test data", "duplicate key"),
            FailureType.DATA_ISSUE,
            "test data",
            "quality engineering",
            "Create isolated deterministic data and clean it transactionally",
        ),
        (
            ("assert", "expected", "status code", "schema"),
            FailureType.APPLICATION_DEFECT,
            "application behavior",
            "product engineering",
            "Reproduce against the acceptance criterion and inspect application logs",
        ),
    ]

    def analyze(self, failure: FailureInput) -> FailureAnalysis:
        text = " ".join(
            [
                failure.test_name,
                failure.error_message,
                failure.stack_trace,
                *failure.browser_console_logs,
            ]
        ).lower()
        statuses = [value.lower() for value in failure.previous_statuses]
        transitions = sum(a != b for a, b in zip(statuses, statuses[1:], strict=False))
        if transitions >= 2 and "passed" in statuses and "failed" in statuses:
            result = self._result(
                FailureType.FLAKY_BEHAVIOR,
                0.88,
                "Recent executions alternate without a code-level signature",
                "test stability",
                "quality engineering",
                "Inspect timing, locators, shared data, ordering, network, and retry evidence",
                [f"{transitions} recent pass/fail transitions"],
                True,
            )
        else:
            result = None
            for keywords, category, component, owner, next_step in self.RULES:
                matches = [word for word in keywords if word in text]
                if matches:
                    result = self._result(
                        category,
                        min(0.95, 0.68 + len(matches) * 0.08),
                        f"Evidence matched {', '.join(matches)}",
                        component,
                        owner,
                        next_step,
                        matches,
                        category in {FailureType.ENVIRONMENT_ISSUE, FailureType.DEPENDENCY_FAILURE},
                    )
                    break
            if result is None:
                result = self._result(
                    FailureType.UNKNOWN,
                    0.3,
                    "Available evidence does not match a deterministic rule",
                    "unknown",
                    "quality triage",
                    "Collect server logs, request/response, trace, and a clean reproduction",
                    [failure.error_message or "no error message supplied"],
                    False,
                )
        FAILURE_CATEGORIES.labels(result.failure_type.value).inc()
        return result

    @staticmethod
    def _result(category, confidence, cause, component, owner, next_step, evidence, retry):
        return FailureAnalysis(
            failure_type=category,
            confidence=confidence,
            probable_cause=cause,
            affected_component=component,
            recommended_owner=owner,
            suggested_next_step=next_step,
            evidence=evidence,
            retry_recommended=retry,
        )
