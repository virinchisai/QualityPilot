from qualitypilot.release_gates.evaluator import (
    ReleaseEvidence,
    ReleaseGateConfig,
    ReleaseGateEvaluator,
)


def test_healthy_release_is_approved():
    decision = ReleaseGateEvaluator().evaluate(ReleaseEvidence(passed_tests=100, total_tests=100))
    assert decision.release_decision == "approved"
    assert not decision.reasons


def test_release_is_blocked_with_specific_reasons():
    decision = ReleaseGateEvaluator().evaluate(
        ReleaseEvidence(
            smoke_failures=["AUTH-SMOKE-001"],
            critical_security_failures=["AUTH-REFRESH-004"],
            passed_tests=90,
            total_tests=100,
            high_confidence_flaky_tests=["UI-LOGIN-009"],
            critical_open_defects=["QP-123"],
        ),
        ReleaseGateConfig(minimum_pass_rate=0.95),
    )
    assert decision.release_decision == "blocked"
    assert len(decision.reasons) == 5
    assert "AUTH-REFRESH-004" in " ".join(decision.reasons)


def test_gate_thresholds_are_configurable():
    decision = ReleaseGateEvaluator().evaluate(
        ReleaseEvidence(
            passed_tests=9,
            total_tests=10,
            high_confidence_flaky_tests=["KNOWN-FLAKY"],
        ),
        ReleaseGateConfig(
            minimum_pass_rate=0.9,
            maximum_high_confidence_flaky_tests=1,
        ),
    )
    assert decision.release_decision == "approved"
