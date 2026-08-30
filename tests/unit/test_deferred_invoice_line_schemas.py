from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from odoo_accounting_cli_v4.registry import (
    CapabilityRegistry,
    InstanceValidationError,
    load_registry,
)

_CAPABILITIES = (
    "customer_invoice.create",
    "vendor_bill.create",
    "invoice.lines.replace",
    "customer_credit_note.create",
    "vendor_refund.create",
)
_DATE_FIELDS = ("deferred_start_date", "deferred_end_date")


@pytest.fixture(scope="module")
def registry() -> CapabilityRegistry:
    return load_registry()


def _request(capability_id: str, dates: dict[str, Any]) -> dict[str, Any]:
    line = {
        "name": "Deferred service",
        "account_id": 31,
        "quantity": "1",
        "price_unit": "120",
        "tax_ids": [],
        **dates,
    }
    if capability_id in {"customer_invoice.create", "vendor_bill.create"}:
        parameters = {
            "partner_id": 21,
            "journal_id": 11,
            "invoice_date": "2026-08-31",
            "currency_id": 1,
            "lines": [line],
        }
    else:
        line.update(product_id=None, discount="0")
        parameters = {"move_id": 101, "lines": [line]}
        if capability_id != "invoice.lines.replace":
            parameters.update(date="2026-08-31", reason="Deferred service refund")
    return {
        "schema_version": "v1",
        "request_id": "7bc39413-0d69-4092-9319-795d33f3167c",
        "context": {
            "database": "v4-dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": parameters,
    }


@pytest.mark.parametrize("capability_id", _CAPABILITIES)
@pytest.mark.parametrize(
    "dates",
    [
        {},
        {"deferred_start_date": None, "deferred_end_date": None},
        {"deferred_start_date": "2026-09-01", "deferred_end_date": "2026-12-31"},
        {"deferred_start_date": "2026-08-31", "deferred_end_date": "2026-08-31"},
        {"deferred_start_date": "2026-01-01", "deferred_end_date": "2026-03-31"},
        {"deferred_start_date": "2028-02-29", "deferred_end_date": "2028-03-31"},
    ],
)
def test_deferred_dates_accept_omission_nulls_and_valid_pairs_without_defaults(
    registry: CapabilityRegistry, capability_id: str, dates: dict[str, Any]
) -> None:
    request = _request(capability_id, dates)
    original = deepcopy(request)
    registry.validate_instance(
        f"schemas/v1/{capability_id}.request.schema.json", request
    )
    assert request == original


@pytest.mark.parametrize("capability_id", _CAPABILITIES)
@pytest.mark.parametrize(
    "dates",
    [
        {"deferred_start_date": "2026-09-01"},
        {"deferred_end_date": "2026-12-31"},
        {"deferred_start_date": None},
        {"deferred_end_date": None},
        {"deferred_start_date": None, "deferred_end_date": "2026-12-31"},
        {"deferred_start_date": "2026-09-01", "deferred_end_date": None},
    ],
)
def test_deferred_dates_require_a_complete_homogeneous_pair(
    registry: CapabilityRegistry, capability_id: str, dates: dict[str, Any]
) -> None:
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(
            f"schemas/v1/{capability_id}.request.schema.json",
            _request(capability_id, dates),
        )


@pytest.mark.parametrize("capability_id", _CAPABILITIES)
@pytest.mark.parametrize("field", _DATE_FIELDS)
@pytest.mark.parametrize(
    "invalid",
    [
        False,
        20260901,
        "2026-9-01",
        "2026-02-29",
        "2026-04-31",
        "2026-09-01T00:00:00Z",
        "2026-09-01\n",
    ],
)
def test_deferred_dates_reject_invalid_or_noncanonical_dates(
    registry: CapabilityRegistry, capability_id: str, field: str, invalid: Any
) -> None:
    dates = {"deferred_start_date": "2026-09-01", "deferred_end_date": "2026-12-31"}
    dates[field] = invalid
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(
            f"schemas/v1/{capability_id}.request.schema.json",
            _request(capability_id, dates),
        )


@pytest.mark.parametrize("capability_id", _CAPABILITIES)
def test_date_order_is_left_to_python_validation(
    registry: CapabilityRegistry, capability_id: str
) -> None:
    registry.validate_instance(
        f"schemas/v1/{capability_id}.request.schema.json",
        _request(
            capability_id,
            {"deferred_start_date": "2026-12-31", "deferred_end_date": "2026-09-01"},
        ),
    )


def test_refunds_reuse_the_identical_closed_replacement_line_schema(
    registry: CapabilityRegistry,
) -> None:
    replacement = registry.load_schema(
        "schemas/v1/invoice.lines.replace.request.schema.json"
    )
    inline = replacement["properties"]["parameters"]["properties"]["lines"]["items"]
    assert inline == replacement["$defs"]["invoice_line"]
    assert inline["additionalProperties"] is False
    assert not set(_DATE_FIELDS) & set(inline["required"])
    for capability_id in ("customer_credit_note.create", "vendor_refund.create"):
        refund = registry.load_schema(f"schemas/v1/{capability_id}.request.schema.json")
        parameters = refund["allOf"][1]["properties"]["parameters"]
        assert parameters["properties"]["lines"]["items"] == {
            "$ref": "invoice.lines.replace.request.schema.json#/$defs/invoice_line"
        }


@pytest.mark.parametrize("capability_id", _CAPABILITIES)
def test_deferred_dates_do_not_open_arbitrary_line_fields(
    registry: CapabilityRegistry, capability_id: str
) -> None:
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(
            f"schemas/v1/{capability_id}.request.schema.json",
            _request(capability_id, {"unexpected_date": "2026-09-01"}),
        )
