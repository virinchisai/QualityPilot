"""Schemathesis-backed OpenAPI operation discovery and response conformance smoke."""

import schemathesis

from app.demo_app.main import app


def test_schemathesis_loads_every_documented_operation():
    schema = schemathesis.openapi.from_asgi("/openapi.json", app)
    operations = list(schema.get_all_operations())
    assert len(operations) >= 9


def test_health_response_conforms_to_documented_success_contract():
    schema = schemathesis.openapi.from_asgi("/openapi.json", app)
    operation = schema["/health"]["GET"]
    case = operation.Case()
    response = case.call()
    case.validate_response(response)
