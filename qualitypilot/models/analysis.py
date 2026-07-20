"""Failure, flaky, and defect report models."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class FailureType(StrEnum):
    APPLICATION_DEFECT = "application_defect"
    TEST_DEFECT = "test_defect"
    FLAKY_BEHAVIOR = "flaky_behavior"
    ENVIRONMENT_ISSUE = "environment_issue"
    DEPENDENCY_FAILURE = "dependency_failure"
    AUTHENTICATION_FAILURE = "authentication_failure"
    AUTHORIZATION_FAILURE = "authorization_failure"
    DATA_ISSUE = "data_issue"
    UNKNOWN = "unknown"


class FailureInput(BaseModel):
    test_name: str
    stack_trace: str = ""
    error_message: str = ""
    http_request: dict[str, Any] | None = None
    http_response: dict[str, Any] | None = None
    screenshot_path: str | None = None
    trace_path: str | None = None
    browser_console_logs: list[str] = Field(default_factory=list)
    duration_seconds: float = 0
    previous_statuses: list[str] = Field(default_factory=list)
    environment: dict[str, Any] = Field(default_factory=dict)


class FailureAnalysis(BaseModel):
    failure_type: FailureType
    confidence: float = Field(ge=0, le=1)
    probable_cause: str
    affected_component: str
    recommended_owner: str
    suggested_next_step: str
    evidence: list[str]
    retry_recommended: bool


class FlakyResult(BaseModel):
    test_id: str
    flakiness_score: float = Field(ge=0, le=1)
    history: list[str]
    probable_cause: str
    suggested_stabilization: str
    is_likely_flaky: bool


class DefectReport(BaseModel):
    defect_id: str
    title: str
    summary: str
    severity: str
    priority: str
    component: str
    environment: dict[str, Any]
    build_commit: str
    preconditions: list[str]
    steps_to_reproduce: list[str]
    expected_result: str
    actual_result: str
    logs: list[str] = Field(default_factory=list)
    screenshot_references: list[str] = Field(default_factory=list)
    video_references: list[str] = Field(default_factory=list)
    trace_references: list[str] = Field(default_factory=list)
    api_request_response: dict[str, Any] | None = None
    suspected_cause: str
    recommended_owner: str
    related_test_case: str
    labels: list[str]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
