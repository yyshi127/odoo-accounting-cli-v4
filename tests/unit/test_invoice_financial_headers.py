from __future__ import annotations

from copy import deepcopy

import pytest
from test_core_writes import FakePort, _request

from odoo_accounting_cli_v4.capabilities.core_writes import (
    CoreWriteError,
    _expected_idempotency_key,
    execute_core_write,
    validate_core_write_request,
)
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

CAPABILITIES = ("customer_invoice.create", "vendor_bill.create", "invoice.update")
FIELDS = ("partner_bank_id", "fiscal_position_id")


@pytest.fixture(scope="module")
def registry():
    return load_registry()


def _with_headers(capability, headers):
    request = _request(capability)
    target = request["parameters"]
    if capability == "invoice.update":
        target = target["changes"]
    target.update(headers)
    return request


@pytest.mark.parametrize("capability", CAPABILITIES)
@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"partner_bank_id": 1},
        {"fiscal_position_id": 2},
        {"partner_bank_id": None},
        {"fiscal_position_id": None},
        {"partner_bank_id": 1, "fiscal_position_id": 2},
        {"partner_bank_id": None, "fiscal_position_id": None},
        {
            "partner_bank_id": 1,
            "fiscal_position_id": None,
            "date": "2026-08-31",
            "journal_id": 4,
            "currency_id": 6,
            "payment_term_id": None,
        },
    ],
)
def test_financial_headers_preserve_explicit_values_and_omission(
    capability, headers, registry
):
    request = _with_headers(capability, headers)
    original = deepcopy(request)
    registry.validate_instance(f"schemas/v1/{capability}.request.schema.json", request)
    _, context, parameters = validate_core_write_request(capability, request)
    assert parameters == original["parameters"]
    key = _expected_idempotency_key(capability, parameters, context["company_id"])
    port = FakePort(capability)
    execute_core_write(
        port, capability, request, key or "financial-header-create", capability
    )
    assert port.calls[0]["parameters"] == original["parameters"]
    assert request == original


@pytest.mark.parametrize("capability", CAPABILITIES)
@pytest.mark.parametrize("field", FIELDS)
@pytest.mark.parametrize("value", [True, False, 0, -1, "1", 1.5, [], {}])
def test_financial_headers_reject_invalid_ids_before_dispatch(
    capability, field, value, registry
):
    request = _with_headers(capability, {field: value})
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(
            f"schemas/v1/{capability}.request.schema.json", request
        )
    port = FakePort(capability)
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(port, capability, request, "invalid-header", capability)
    assert caught.value.code == "invalid_request"
    assert port.calls == []


@pytest.mark.parametrize("capability", CAPABILITIES)
@pytest.mark.parametrize("field", FIELDS)
def test_financial_headers_reject_integral_python_floats(capability, field):
    with pytest.raises(CoreWriteError, match="positive integer"):
        validate_core_write_request(capability, _with_headers(capability, {field: 1.0}))


@pytest.mark.parametrize("field", FIELDS)
@pytest.mark.parametrize("value", [None, 1, 2])
def test_update_key_binds_new_header_presence_and_value(field, value):
    capability = "invoice.update"
    original = _with_headers(capability, {})
    request = _with_headers(capability, {field: value})
    key = _expected_idempotency_key(capability, original["parameters"], 1)
    new_key = _expected_idempotency_key(capability, request["parameters"], 1)
    assert key != new_key
    changed = deepcopy(request)
    changed["parameters"]["changes"][field] = 3
    assert new_key != _expected_idempotency_key(capability, changed["parameters"], 1)
    port = FakePort(capability)
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(port, capability, request, key, capability)
    assert caught.value.code == "invalid_idempotency_key"
    assert port.calls == []
