#!/usr/bin/env python3
"""Evaluate CI JUnit evidence through the QualityPilot release gate."""

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from qualitypilot.release_gates.evaluator import (
    ReleaseEvidence,
    ReleaseGateConfig,
    ReleaseGateEvaluator,
)


def counts_from_junit(path: Path) -> tuple[int, int]:
    root = ET.parse(path).getroot()  # noqa: S314 - trusted local CI artifact
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    total = sum(int(suite.attrib.get("tests", 0)) for suite in suites)
    not_passed = sum(
        int(suite.attrib.get(name, 0))
        for suite in suites
        for name in ("failures", "errors", "skipped")
    )
    return total - not_passed, total


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--junit", type=Path, required=True)
    parser.add_argument("--minimum-pass-rate", type=float, default=0.95)
    parser.add_argument("--output", type=Path, default=Path("reports/release-gate.json"))
    args = parser.parse_args()

    passed, total = counts_from_junit(args.junit)
    decision = ReleaseGateEvaluator().evaluate(
        ReleaseEvidence(passed_tests=passed, total_tests=total),
        ReleaseGateConfig(minimum_pass_rate=args.minimum_pass_rate),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(decision.model_dump_json(indent=2), encoding="utf-8")
    print(decision.model_dump_json(indent=2))
    return 0 if decision.release_decision == "approved" else 1


if __name__ == "__main__":
    sys.exit(main())
