"""Validated requirement and test-case domain models."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class TestType(StrEnum):
    FUNCTIONAL = "functional"
    NEGATIVE = "negative"
    BOUNDARY = "boundary"
    REGRESSION = "regression"
    SMOKE = "smoke"
    INTEGRATION = "integration"
    SECURITY = "security"
    API = "api"
    UI = "ui"
    E2E = "e2e"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    ACCESSIBILITY = "accessibility"
    PERFORMANCE = "performance"
    AI_QUALITY = "ai_quality"


class Requirement(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=250)
    description: str = Field(min_length=1)
    acceptance_criteria: list[str] = Field(default_factory=list)
    source_format: str = "text"
    metadata: dict[str, Any] = Field(default_factory=dict)


class TestStep(BaseModel):
    action: str
    expected: str | None = None


class TestCase(BaseModel):
    test_id: str
    title: str
    description: str
    requirement_id: str
    preconditions: list[str]
    test_data: dict[str, Any]
    test_steps: list[TestStep]
    expected_result: str
    test_type: TestType
    priority: str
    severity: str
    tags: list[str]
    automation_candidate: bool
    related_endpoint: str | None = None
    related_ui_page: str | None = None


class GenerationResult(BaseModel):
    requirement: Requirement
    test_cases: list[TestCase]
    gherkin: str
