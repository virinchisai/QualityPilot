"""Configurable release-level quality gate evaluation."""

from typing import Literal

from pydantic import BaseModel, Field


class ReleaseGateConfig(BaseModel):
    minimum_pass_rate: float = Field(default=0.95, ge=0, le=1)
    maximum_high_confidence_flaky_tests: int = Field(default=0, ge=0)
    block_on_smoke_failure: bool = True
    block_on_critical_security_failure: bool = True
    block_on_critical_open_defect: bool = True


class ReleaseEvidence(BaseModel):
    smoke_failures: list[str] = Field(default_factory=list)
    critical_security_failures: list[str] = Field(default_factory=list)
    passed_tests: int = Field(default=0, ge=0)
    total_tests: int = Field(default=0, ge=0)
    high_confidence_flaky_tests: list[str] = Field(default_factory=list)
    critical_open_defects: list[str] = Field(default_factory=list)


class ReleaseDecision(BaseModel):
    release_decision: Literal["approved", "blocked"]
    pass_rate: float = Field(ge=0, le=1)
    reasons: list[str]
    evaluated_gates: dict[str, bool]


class ReleaseGateEvaluator:
    def evaluate(
        self, evidence: ReleaseEvidence, config: ReleaseGateConfig | None = None
    ) -> ReleaseDecision:
        settings = config or ReleaseGateConfig()
        pass_rate = evidence.passed_tests / evidence.total_tests if evidence.total_tests else 0.0
        gates = {
            "smoke_suite": not evidence.smoke_failures,
            "critical_security": not evidence.critical_security_failures,
            "pass_rate": pass_rate >= settings.minimum_pass_rate,
            "flaky_tests": len(evidence.high_confidence_flaky_tests)
            <= settings.maximum_high_confidence_flaky_tests,
            "critical_defects": not evidence.critical_open_defects,
        }
        reasons = []
        if settings.block_on_smoke_failure and not gates["smoke_suite"]:
            reasons.append("Smoke failures: " + ", ".join(evidence.smoke_failures))
        if settings.block_on_critical_security_failure and not gates["critical_security"]:
            reasons.append(
                "Critical security failures: " + ", ".join(evidence.critical_security_failures)
            )
        if not gates["pass_rate"]:
            reasons.append(
                f"Pass rate {pass_rate:.1%} is below the {settings.minimum_pass_rate:.1%} threshold"
            )
        if not gates["flaky_tests"]:
            reasons.append(
                "High-confidence flaky tests exceed threshold: "
                + ", ".join(evidence.high_confidence_flaky_tests)
            )
        if settings.block_on_critical_open_defect and not gates["critical_defects"]:
            reasons.append("Critical open defects: " + ", ".join(evidence.critical_open_defects))
        return ReleaseDecision(
            release_decision="blocked" if reasons else "approved",
            pass_rate=round(pass_rate, 4),
            reasons=reasons,
            evaluated_gates=gates,
        )
