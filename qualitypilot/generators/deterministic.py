"""Traceable, offline test-case and Gherkin generation."""

import re

from qualitypilot.adapters.base import TestCaseGeneratorAdapter
from qualitypilot.models.test_case import (
    GenerationResult,
    Requirement,
    TestCase,
    TestStep,
    TestType,
)


class DeterministicTestGenerator(TestCaseGeneratorAdapter):
    def generate(self, requirement: Requirement) -> GenerationResult:
        slug = re.sub(r"[^A-Z0-9]+", "-", requirement.id.upper()).strip("-")
        endpoint = requirement.metadata.get("endpoint") or self._endpoint(requirement)
        page = "/" if "login" in requirement.title.lower() else None
        cases = [
            self._case(
                slug,
                1,
                requirement,
                "Happy path",
                TestType.FUNCTIONAL,
                "high",
                "major",
                endpoint,
                page,
                [
                    TestStep(action="Arrange valid preconditions and representative data"),
                    TestStep(action="Perform the requested behavior"),
                ],
                requirement.acceptance_criteria[0]
                if requirement.acceptance_criteria
                else "The requirement succeeds as described",
            ),
            self._case(
                slug,
                2,
                requirement,
                "Invalid input is rejected",
                TestType.NEGATIVE,
                "high",
                "major",
                endpoint,
                page,
                [
                    TestStep(action="Prepare an invalid or missing required value"),
                    TestStep(action="Submit the request"),
                ],
                "The system rejects the input with a safe, actionable error",
            ),
            self._case(
                slug,
                3,
                requirement,
                "Boundary values",
                TestType.BOUNDARY,
                "medium",
                "minor",
                endpoint,
                page,
                [
                    TestStep(action="Prepare minimum, maximum, and just-outside-boundary values"),
                    TestStep(action="Submit each value"),
                ],
                "Valid boundaries pass and invalid boundaries are rejected",
            ),
        ]
        if any(
            word in (requirement.title + requirement.description).lower()
            for word in ("login", "token", "admin", "role", "auth")
        ):
            cases.append(
                self._case(
                    slug,
                    4,
                    requirement,
                    "Identity and access control",
                    TestType.SECURITY,
                    "critical",
                    "critical",
                    endpoint,
                    page,
                    [
                        TestStep(
                            action=(
                                "Call without, with malformed, and with "
                                "insufficient-role credentials"
                            )
                        ),
                        TestStep(action="Repeat with valid authorized credentials"),
                    ],
                    "Unauthorized calls are denied and only the intended role succeeds",
                )
            )
        return GenerationResult(
            requirement=requirement, test_cases=cases, gherkin=self.to_gherkin(requirement, cases)
        )

    def _case(
        self,
        slug,
        number,
        req,
        suffix,
        test_type,
        priority,
        severity,
        endpoint,
        page,
        steps,
        expected,
    ):
        return TestCase(
            test_id=f"TC-{slug}-{number:03d}",
            title=f"{req.title} — {suffix}",
            description=f"Validate {suffix.lower()} for {req.title}.",
            requirement_id=req.id,
            preconditions=["The demo application is healthy", "Test data is isolated"],
            test_data={"data_version": "v1", "source": "deterministic"},
            test_steps=steps,
            expected_result=expected,
            test_type=test_type,
            priority=priority,
            severity=severity,
            tags=[req.id, test_type.value, "generated"],
            automation_candidate=True,
            related_endpoint=endpoint,
            related_ui_page=page,
        )

    @staticmethod
    def _endpoint(requirement: Requirement) -> str | None:
        text = (requirement.title + requirement.description).lower()
        return next(
            (
                value
                for key, value in {
                    "login": "/api/login",
                    "refresh": "/api/token/refresh",
                    "logout": "/api/logout",
                    "profile": "/api/me",
                    "admin": "/api/admin/audit",
                }.items()
                if key in text
            ),
            None,
        )

    @staticmethod
    def to_gherkin(requirement: Requirement, cases: list[TestCase]) -> str:
        lines = [
            f"@requirement_{re.sub(r'[^A-Za-z0-9_]', '_', requirement.id)}",
            f"Feature: {requirement.title}",
            f"  {requirement.description.splitlines()[0]}",
            "",
        ]
        for case in cases:
            lines += [
                f"  @{case.test_type.value} @test_{case.test_id.replace('-', '_')}",
                f"  Scenario: {case.title}",
                "    Given the demo application is healthy",
            ]
            for step in case.test_steps:
                lines.append(f"    When {step.action.lower()}")
            lines += [f"    Then {case.expected_result}", ""]
        return "\n".join(lines)
