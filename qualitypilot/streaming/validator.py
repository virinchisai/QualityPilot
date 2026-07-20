"""Lightweight Kafka-compatible event semantics validator."""

from collections import defaultdict
from typing import Any

from jsonschema import Draft202012Validator


def validate_events(events: list[dict[str, Any]], schema: dict[str, Any]) -> dict[str, Any]:
    validator = Draft202012Validator(schema)
    seen: set[str] = set()
    last_sequence: dict[str, int] = defaultdict(lambda: -1)
    duplicates, out_of_order, invalid, dead_letter = [], [], [], []
    for event in events:
        errors = [error.message for error in validator.iter_errors(event)]
        if errors:
            invalid.append({"event": event, "errors": errors})
            dead_letter.append(event)
            continue
        event_id, key, sequence = event["event_id"], event["aggregate_id"], event["sequence"]
        if event_id in seen:
            duplicates.append(event_id)
        if sequence <= last_sequence[key]:
            out_of_order.append(event_id)
        seen.add(event_id)
        last_sequence[key] = max(sequence, last_sequence[key])
    return {
        "valid": not (duplicates or out_of_order or invalid),
        "duplicates": duplicates,
        "out_of_order": out_of_order,
        "invalid": invalid,
        "dead_letter": dead_letter,
    }
