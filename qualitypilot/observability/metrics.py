"""Prometheus metrics shared by the APIs."""

from prometheus_client import Counter, Histogram

HTTP_REQUESTS = Counter(
    "qualitypilot_http_requests_total", "HTTP requests", ["app", "method", "path", "status"]
)
HTTP_LATENCY = Histogram(
    "qualitypilot_http_request_duration_seconds", "HTTP latency", ["app", "method", "path"]
)
TEST_EXECUTIONS = Counter(
    "qualitypilot_test_executions_total", "Recorded test executions", ["status"]
)
FAILURE_CATEGORIES = Counter(
    "qualitypilot_failure_categories_total", "Classified failures", ["category"]
)
FLAKY_TESTS = Counter("qualitypilot_flaky_tests_detected_total", "Likely flaky tests detected")
