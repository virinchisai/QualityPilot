from qualitypilot.streaming.validator import validate_events

SCHEMA = {
    "type": "object",
    "required": ["event_id", "aggregate_id", "sequence"],
    "properties": {
        "event_id": {"type": "string"},
        "aggregate_id": {"type": "string"},
        "sequence": {"type": "integer"},
    },
}


def test_duplicate_order_and_dead_letter_detection():
    events = [
        {"event_id": "1", "aggregate_id": "A", "sequence": 1},
        {"event_id": "1", "aggregate_id": "A", "sequence": 1},
        {"event_id": "bad"},
    ]
    result = validate_events(events, SCHEMA)
    assert not result["valid"] and result["duplicates"] == ["1"]
    assert result["out_of_order"] == ["1"] and result["dead_letter"] == [{"event_id": "bad"}]
