"""Rally-compatible test-case export without requiring a Rally account."""

import csv
import io
import json
from typing import Any

from qualitypilot.models.test_case import TestCase


class RallyTestCaseExporter:
    """Map QualityPilot cases to import-friendly Rally field names."""

    FIELDNAMES = [
        "FormattedID",
        "Name",
        "WorkProduct",
        "Type",
        "Priority",
        "PreConditions",
        "Steps",
        "ExpectedResult",
        "Method",
        "Tags",
    ]

    def to_record(self, test_case: TestCase) -> dict[str, Any]:
        steps = [
            {
                "StepIndex": index,
                "Input": step.action,
                "ExpectedResult": step.expected or "",
            }
            for index, step in enumerate(test_case.test_steps, start=1)
        ]
        return {
            "FormattedID": test_case.test_id,
            "Name": test_case.title,
            "WorkProduct": test_case.requirement_id,
            "Type": test_case.test_type.value.replace("_", " ").title(),
            "Priority": test_case.priority.title(),
            "PreConditions": "\n".join(test_case.preconditions),
            "Steps": steps,
            "ExpectedResult": test_case.expected_result,
            "Method": "Automated" if test_case.automation_candidate else "Manual",
            "Tags": ",".join(test_case.tags),
        }

    def to_json(self, test_cases: list[TestCase]) -> str:
        return json.dumps([self.to_record(case) for case in test_cases], indent=2)

    def to_csv(self, test_cases: list[TestCase]) -> str:
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=self.FIELDNAMES)
        writer.writeheader()
        for test_case in test_cases:
            record = self.to_record(test_case)
            record["Steps"] = json.dumps(record["Steps"])
            writer.writerow(record)
        return buffer.getvalue()
