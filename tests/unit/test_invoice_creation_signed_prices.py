from __future__ import annotations

from copy import deepcopy

import pytest
from test_core_writes import FakePort, _key, _request

from odoo_accounting_cli_v4.capabilities.core_writes import (
    CoreWriteError,
    execute_core_write,
    validate_core_write_request,
)
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

CAPABILITIES = ("customer_invoice.create", "vendor_bill.create")


@pytest.fixture(scope="module")
def registry():
    return load_registry()


def _adjusted_request(capability_id, prices=("100", "-10")):
    request = _request(capability_id)
    line = request["parameters"]["lines"][0]
    request["parameters"]["lines"] = [
        {**line, "name": name, "quantity": "1", "price_unit": price, "tax_ids": []}
        for name, price in zip(("Base amount", "Adjustment"), prices, strict=True)
    ]
    return request


@pytest.mark.parametrize("capability_id", CAPABILITIES)
@pytest.mark.parametrize(
    "prices",
    [
        pytest.param(("100", "-10"), id="100-minus-10"),
        pytest.param(("100.00", "-10.00"), id="existing-decimal-scale"),
        pytest.param(("0", "-0"), id="same-signed-zero-rule-as-replacement"),
        pytest.param(("10", "-20"), id="no-new-total-amount-policy"),
        pytest.param(("1", "-" + "9" * 255), id="256-character-boundary"),
    ],
)
def test_invoice_creation_passes_signed_prices_unchanged(
    capability_id, prices, registry
):
    request = _adjusted_request(capability_id, prices)
    original = deepcopy(request)
    _, _, parameters = validate_core_write_request(capability_id, request)
    assert parameters == original["parameters"]
    registry.validate_instance(
        f"schemas/v1/{capability_id}.request.schema.json", request
    )

    port = FakePort(capability_id)
    execute_core_write(port, capability_id, request, _key(capability_id), capability_id)
    assert port.calls[0]["parameters"] == original["parameters"]
    assert request == original


@pytest.mark.parametrize("capability_id", CAPABILITIES)
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("quantity", "0"),
        ("quantity", "-1"),
        ("quantity", True),
        ("price_unit", "-01"),
        ("price_unit", "-1e2"),
        ("price_unit", "NaN"),
        ("price_unit", "-Infinity"),
        ("price_unit", -10),
        ("price_unit", False),
        ("price_unit", " -10"),
        ("price_unit", "-10\n"),
        ("price_unit", "-" + "9" * 256),
        ("discount", "-1"),
        ("discount", "100.01"),
        ("unexpected", True),
    ],
)
def test_invoice_creation_retains_quantity_decimal_discount_and_field_boundaries(
    capability_id, field, value, registry
):
    request = _adjusted_request(capability_id)
    request["parameters"]["lines"][1][field] = value
    original = deepcopy(request)
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(
            f"schemas/v1/{capability_id}.request.schema.json", request
        )
    port = FakePort(capability_id)
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            port, capability_id, request, _key(capability_id), capability_id
        )
    assert caught.value.code == "invalid_request" and caught.value.exit_code == 2
    assert port.calls == [] and request == original
