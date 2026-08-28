from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from odoo_accounting_cli_v4.capabilities.inventory_accounting import (
    INVENTORY_ACCOUNTING_CAPABILITY_IDS,
    InventoryAccountingError,
    read_inventory_accounting,
    validate_inventory_accounting_request,
)
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

REQUEST_ID = "123e4567-e89b-42d3-a456-426614174000"
CAPABILITIES = (
    "cogs.entries.list",
    "inventory.accounting_entries.list",
    "report.inventory_valuation",
    "purchase_bill.matching.inspect",
    "sale_invoice.stock_link.inspect",
)
MODELS = {
    "cogs.entries.list": "account.move.line",
    "inventory.accounting_entries.list": "stock.move",
    "report.inventory_valuation": "stock_account.stock.valuation.report",
    "purchase_bill.matching.inspect": "account.move",
    "sale_invoice.stock_link.inspect": "account.move",
}


def _request(
    capability_id: str,
    parameters: dict[str, Any] | None = None,
    *,
    company_id: int = 7,
) -> dict[str, Any]:
    defaults: dict[str, dict[str, Any]] = {
        "cogs.entries.list": {},
        "inventory.accounting_entries.list": {},
        "report.inventory_valuation": {},
        "purchase_bill.matching.inspect": {"bill_id": 41},
        "sale_invoice.stock_link.inspect": {"invoice_id": 51},
    }
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "context": {
            "database": "odoo_cli_v4_dev",
            "company_id": company_id,
            "user_login": "cli.accounting",
            "language": "en_US",
            "timezone": "UTC",
        },
        "parameters": deepcopy(
            defaults[capability_id] if parameters is None else parameters
        ),
    }


def _page(
    items: list[dict[str, Any]] | None = None,
    **changes: Any,
) -> dict[str, Any]:
    page = {
        "user_id": 5,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "cursor_found": True,
        "items": items or [],
    }
    page.update(changes)
    return page


class FakePort:
    def __init__(self, page: dict[str, Any], *, user_id: int = 5) -> None:
        self.page = page
        self.user_id = user_id
        self.calls: list[dict[str, Any]] = []

    def read(
        self,
        *,
        capability_id: str,
        company_id: int,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "capability_id": capability_id,
                "company_id": company_id,
                "parameters": deepcopy(parameters),
            }
        )
        return deepcopy(self.page)


def _account(record_id: int = 601) -> dict[str, Any]:
    return {"id": record_id, "code": str(record_id), "name": "Stock account"}


def _currency() -> dict[str, Any]:
    return {"id": 2, "code": "USD"}


def _cogs(record_id: int, entry_date: str, **changes: Any) -> dict[str, Any]:
    row = {
        "id": record_id,
        "date": entry_date,
        "company_id": 7,
        "invoice": {
            "id": 51,
            "name": "INV/2025/0051",
            "move_type": "out_invoice",
            "state": "posted",
        },
        "origin_invoice_line_id": 151,
        "account": _account(),
        "product": {"id": 31, "name": "Desk"},
        "label": "Cost of goods sold",
        "quantity": "2.00",
        "debit": "25.50",
        "credit": "0",
        "balance": "25.50",
        "company_currency": _currency(),
        "sale_order_line_ids": [201],
        "stock_move_ids": [301],
    }
    row.update(changes)
    return row


def _lines() -> list[dict[str, Any]]:
    return [
        {
            "id": 701,
            "account": _account(601),
            "debit": "25.50",
            "credit": "0",
            "balance": "25.50",
        },
        {
            "id": 702,
            "account": _account(602),
            "debit": "0",
            "credit": "25.50",
            "balance": "-25.50",
        },
    ]


def _inventory(record_id: int, move_date: str, **changes: Any) -> dict[str, Any]:
    row = {
        "id": record_id,
        "date": move_date,
        "company_id": 7,
        "reference": "WH/OUT/0031",
        "state": "done",
        "product": {"id": 31, "name": "Desk"},
        "quantity": "2.00",
        "uom": {"id": 1, "name": "Units"},
        "value": "25.50",
        "is_in": False,
        "is_out": True,
        "account_move": {
            "id": 501,
            "name": "STJ/2025/0501",
            "date": "2025-01-31",
            "state": "posted",
            "journal": {"id": 8, "code": "STJ", "name": "Stock Journal"},
        },
        "lines": _lines(),
        "company_currency": _currency(),
    }
    row.update(changes)
    return row


def _valuation(**changes: Any) -> dict[str, Any]:
    row = {
        "as_of_date": "2025-01-31",
        "company": {"id": 7, "name": "Example Company"},
        "currency": _currency(),
        "initial_balance": "20.00",
        "ending_stock": "25.50",
        "stock_variation": "5.50",
        "inventory_loss": None,
        "not_invoiced_delivered_goods": None,
        "not_invoiced_received_goods": None,
        "cost_of_production": None,
        "accounts": [
            {
                "account": _account(),
                "initial_balance": "20.00",
                "ending_stock": "25.50",
                "variation_debit": "5.50",
                "variation_credit": "0",
            }
        ],
    }
    row.update(changes)
    return row


def _purchase(**changes: Any) -> dict[str, Any]:
    row = {
        "id": 41,
        "name": "BILL/2025/0041",
        "move_type": "in_invoice",
        "state": "posted",
        "company_id": 7,
        "partner": {"id": 11, "name": "Supplier"},
        "currency": _currency(),
        "is_purchase_matched": False,
        "purchase_order_ids": [],
        "lines": [
            {
                "id": 141,
                "product": {"id": 31, "name": "Desk"},
                "label": "Desk",
                "quantity": "2.00",
                "price_subtotal": "25.50",
                "purchase_line": None,
                "unmatched_queue": True,
            }
        ],
    }
    row.update(changes)
    return row


def _sale(**changes: Any) -> dict[str, Any]:
    accounting_entry = {
        "id": 501,
        "name": "STJ/2025/0501",
        "date": "2025-01-31",
        "state": "posted",
        "lines": _lines(),
    }
    stock_move = {
        "id": 301,
        "date": "2025-01-31T12:30:00Z",
        "state": "done",
        "reference": "WH/OUT/0031",
        "product": {"id": 31, "name": "Desk"},
        "quantity": "2.00",
        "uom": {"id": 1, "name": "Units"},
        "value": "25.50",
        "accounting_entry": accounting_entry,
    }
    row = {
        "id": 51,
        "name": "INV/2025/0051",
        "move_type": "out_invoice",
        "state": "posted",
        "company_id": 7,
        "lines": [
            {
                "id": 151,
                "product": {"id": 31, "name": "Desk"},
                "quantity": "2.00",
                "sale_order_line_ids": [201],
                "stock_moves": [stock_move],
            }
        ],
        "stock_move_ids": [301],
        "account_move_ids": [501],
    }
    row.update(changes)
    return row


def test_capability_set_and_normalized_requests_are_closed() -> None:
    assert INVENTORY_ACCOUNTING_CAPABILITY_IDS == frozenset(CAPABILITIES)
    cases = {
        "cogs.entries.list": (
            {"date_from": "2025-01-01", "invoice_id": 51, "limit": 20},
            {
                "date_from": "2025-01-01",
                "date_to": None,
                "invoice_id": 51,
                "product_id": None,
                "limit": 20,
                "cursor": None,
            },
        ),
        "inventory.accounting_entries.list": (
            {"product_id": 31},
            {
                "date_from": None,
                "date_to": None,
                "product_id": 31,
                "limit": 100,
                "cursor": None,
            },
        ),
        "report.inventory_valuation": ({}, {"date": None}),
        "purchase_bill.matching.inspect": ({"bill_id": 41}, {"bill_id": 41}),
        "sale_invoice.stock_link.inspect": (
            {"invoice_id": 51},
            {"invoice_id": 51},
        ),
    }
    for capability_id, (raw, expected) in cases.items():
        request_id, context, parameters = validate_inventory_accounting_request(
            capability_id, _request(capability_id, raw)
        )
        assert request_id == REQUEST_ID
        assert context["company_id"] == 7
        assert parameters == expected


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    [
        ("cogs.entries.list", {"date_from": "2025-02-01", "date_to": "2025-01-31"}),
        ("cogs.entries.list", {"product_id": True}),
        ("inventory.accounting_entries.list", {"limit": 1001}),
        ("inventory.accounting_entries.list", {"cursor": ""}),
        ("report.inventory_valuation", {"date": "2025-02-30"}),
        ("report.inventory_valuation", {"extra": True}),
        ("purchase_bill.matching.inspect", {"bill_id": -1}),
        ("sale_invoice.stock_link.inspect", {"invoice_id": 51, "extra": True}),
    ],
)
def test_invalid_requests_never_reach_the_port(
    capability_id: str, parameters: dict[str, Any]
) -> None:
    port = FakePort(_page())
    with pytest.raises(InventoryAccountingError) as caught:
        read_inventory_accounting(
            capability_id, port, _request(capability_id, parameters)
        )
    assert caught.value.code == "invalid_request"
    assert caught.value.exit_code == 2
    assert port.calls == []


def test_cogs_list_uses_filter_bound_date_id_keyset_pagination() -> None:
    rows = [
        _cogs(92, "2025-01-31"),
        _cogs(91, "2025-01-31"),
        _cogs(90, "2025-01-30"),
    ]
    first_port = FakePort(_page(rows))
    request = _request(
        "cogs.entries.list",
        {"invoice_id": 51, "product_id": 31, "limit": 2},
    )

    first = read_inventory_accounting("cogs.entries.list", first_port, request)

    assert first["items"] == rows[:2]
    assert first["has_more"] is True
    assert isinstance(first["next_cursor"], str)
    assert first_port.calls == [
        {
            "capability_id": "cogs.entries.list",
            "company_id": 7,
            "parameters": {
                "date_from": None,
                "date_to": None,
                "invoice_id": 51,
                "product_id": 31,
                "after": None,
                "limit": 3,
            },
        }
    ]

    second_port = FakePort(_page([rows[2]]))
    second_request = deepcopy(request)
    second_request["parameters"]["cursor"] = first["next_cursor"]
    second = read_inventory_accounting("cogs.entries.list", second_port, second_request)
    assert second == {"items": [rows[2]], "has_more": False, "next_cursor": None}
    assert second_port.calls[0]["parameters"]["after"] == ["2025-01-31", 91]

    changed_filter = deepcopy(second_request)
    changed_filter["parameters"]["product_id"] = 32
    with pytest.raises(InventoryAccountingError) as caught:
        read_inventory_accounting(
            "cogs.entries.list", FakePort(_page()), changed_filter
        )
    assert caught.value.code == "invalid_cursor"


def test_inventory_entries_have_a_distinct_datetime_cursor_contract() -> None:
    rows = [
        _inventory(302, "2025-01-31T12:30:00Z"),
        _inventory(301, "2025-01-31T12:29:59Z"),
    ]
    port = FakePort(_page(rows))
    result = read_inventory_accounting(
        "inventory.accounting_entries.list",
        port,
        _request(
            "inventory.accounting_entries.list",
            {"date_from": "2025-01-01", "date_to": "2025-01-31", "limit": 1},
        ),
    )
    assert result["items"] == rows[:1]
    assert result["has_more"] is True
    assert result["next_cursor"]

    bad_boundary_port = FakePort(_page([], cursor_found=False))
    request = _request(
        "inventory.accounting_entries.list",
        {"date_from": "2025-01-01", "date_to": "2025-01-31", "limit": 1},
    )
    request["parameters"]["cursor"] = result["next_cursor"]
    with pytest.raises(InventoryAccountingError) as caught:
        read_inventory_accounting(
            "inventory.accounting_entries.list", bad_boundary_port, request
        )
    assert caught.value.code == "invalid_cursor"


def test_valuation_purchase_and_sale_success_shapes_are_preserved() -> None:
    cases = (
        ("report.inventory_valuation", {"date": "2025-01-31"}, _valuation()),
        ("purchase_bill.matching.inspect", {"bill_id": 41}, _purchase()),
        ("sale_invoice.stock_link.inspect", {"invoice_id": 51}, _sale()),
    )
    for capability_id, parameters, expected in cases:
        port = FakePort(_page([expected]))
        assert (
            read_inventory_accounting(
                capability_id, port, _request(capability_id, parameters)
            )
            == expected
        )
        assert port.calls == [
            {
                "capability_id": capability_id,
                "company_id": 7,
                "parameters": parameters,
            }
        ]


def test_honest_empty_relation_shapes_are_valid() -> None:
    zero_valuation = _valuation(
        initial_balance="0",
        ending_stock="0",
        stock_variation="0",
        accounts=[],
    )
    empty_sale = _sale(
        lines=[
            {
                "id": 151,
                "product": {"id": 31, "name": "Desk"},
                "quantity": "2.00",
                "sale_order_line_ids": [],
                "stock_moves": [],
            }
        ],
        stock_move_ids=[],
        account_move_ids=[],
    )
    for capability_id, parameters, row in (
        ("report.inventory_valuation", {"date": "2025-01-31"}, zero_valuation),
        ("sale_invoice.stock_link.inspect", {"invoice_id": 51}, empty_sale),
    ):
        result = read_inventory_accounting(
            capability_id,
            FakePort(_page([row])),
            _request(capability_id, parameters),
        )
        assert result == row


def test_purchase_match_uses_only_positive_odoo_relation_ids() -> None:
    matched_line = deepcopy(_purchase()["lines"][0])
    matched_line.update(
        purchase_line={
            "id": 241,
            "order_id": 341,
            "ordered_quantity": "2",
            "received_quantity": "2",
            "invoiced_quantity": "2",
            "to_invoice_quantity": "0",
        },
        unmatched_queue=False,
    )
    matched = _purchase(
        is_purchase_matched=True,
        purchase_order_ids=[341],
        lines=[matched_line],
    )
    result = read_inventory_accounting(
        "purchase_bill.matching.inspect",
        FakePort(_page([matched])),
        _request("purchase_bill.matching.inspect"),
    )
    assert result == matched
    assert set(result) == {
        "id",
        "name",
        "move_type",
        "state",
        "company_id",
        "partner",
        "currency",
        "is_purchase_matched",
        "purchase_order_ids",
        "lines",
    }
    assert all(line["id"] > 0 for line in result["lines"])


@pytest.mark.parametrize(
    ("page", "code", "exit_code"),
    [
        (_page(company_visible=False, access_allowed=False), "company_unavailable", 3),
        (_page(module_installed=False, access_allowed=False), "uninstalled", 4),
        (_page(access_allowed=False), "unauthorized", 3),
    ],
)
def test_access_gates_fail_closed(
    page: dict[str, Any], code: str, exit_code: int
) -> None:
    with pytest.raises(InventoryAccountingError) as caught:
        read_inventory_accounting(
            "cogs.entries.list", FakePort(page), _request("cogs.entries.list")
        )
    assert caught.value.code == code
    assert caught.value.exit_code == exit_code


@pytest.mark.parametrize(
    ("capability_id", "row"),
    [
        ("cogs.entries.list", _cogs(92, "2025-01-31", company_id=8)),
        ("cogs.entries.list", _cogs(92, "2025-01-31", debit=25.5)),
        (
            "inventory.accounting_entries.list",
            _inventory(302, "2025-01-31 12:30:00"),
        ),
        (
            "report.inventory_valuation",
            _valuation(stock_variation="6.00"),
        ),
        (
            "purchase_bill.matching.inspect",
            _purchase(is_purchase_matched=True),
        ),
        (
            "sale_invoice.stock_link.inspect",
            _sale(account_move_ids=[]),
        ),
    ],
)
def test_invalid_odoo_rows_never_become_verified(
    capability_id: str, row: dict[str, Any]
) -> None:
    with pytest.raises(InventoryAccountingError) as caught:
        read_inventory_accounting(
            capability_id,
            FakePort(_page([row])),
            _request(capability_id),
        )
    assert caught.value.code == "failed_validation"
    assert caught.value.exit_code == 8


def test_duplicate_or_unstable_list_rows_fail_closed() -> None:
    for rows in (
        [_cogs(91, "2025-01-31"), _cogs(92, "2025-01-31")],
        [_cogs(92, "2025-01-31"), _cogs(92, "2025-01-30")],
    ):
        with pytest.raises(InventoryAccountingError) as caught:
            read_inventory_accounting(
                "cogs.entries.list",
                FakePort(_page(rows)),
                _request("cogs.entries.list"),
            )
        assert caught.value.code == "failed_validation"


def test_wrong_user_page_shape_and_missing_inspection_fail_closed() -> None:
    with pytest.raises(InventoryAccountingError) as caught:
        read_inventory_accounting(
            "cogs.entries.list",
            FakePort(_page(), user_id=6),
            _request("cogs.entries.list"),
        )
    assert caught.value.code == "failed_validation"

    malformed = _page()
    malformed["extra"] = True
    with pytest.raises(InventoryAccountingError) as caught:
        read_inventory_accounting(
            "cogs.entries.list",
            FakePort(malformed),
            _request("cogs.entries.list"),
        )
    assert caught.value.code == "failed_validation"

    with pytest.raises(InventoryAccountingError) as caught:
        read_inventory_accounting(
            "purchase_bill.matching.inspect",
            FakePort(_page()),
            _request("purchase_bill.matching.inspect"),
        )
    assert caught.value.code == "record_not_found"
    assert caught.value.exit_code == 4


def _response(capability_id: str, data: dict[str, Any]) -> dict[str, Any]:
    record_ids = (
        [item["id"] for item in data["items"]]
        if capability_id
        in {
            "cogs.entries.list",
            "inventory.accounting_entries.list",
        }
        else (
            [data["id"]]
            if capability_id
            in {"purchase_bill.matching.inspect", "sale_invoice.stock_link.inspect"}
            else []
        )
    )
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "success": True,
        "capability": capability_id,
        "status": "verified",
        "data": data,
        "warnings": [],
        "error": None,
        "odoo": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_id": 5,
            "model": MODELS[capability_id],
            "record_ids": record_ids,
        },
        "audit": {
            "operation_id": None,
            "idempotency_key": None,
            "verification": {"mode": "read_only"},
        },
    }


def test_all_five_schema_pairs_validate_the_frozen_contracts() -> None:
    root = Path(__file__).resolve().parents[2]
    registry = load_registry()
    data = {
        "cogs.entries.list": {
            "items": [_cogs(92, "2025-01-31")],
            "has_more": False,
            "next_cursor": None,
        },
        "inventory.accounting_entries.list": {
            "items": [_inventory(302, "2025-01-31T12:30:00Z")],
            "has_more": False,
            "next_cursor": None,
        },
        "report.inventory_valuation": _valuation(),
        "purchase_bill.matching.inspect": _purchase(),
        "sale_invoice.stock_link.inspect": _sale(),
    }
    for capability_id in CAPABILITIES:
        request_schema = f"schemas/v1/{capability_id}.request.schema.json"
        response_schema = f"schemas/v1/{capability_id}.response.schema.json"
        assert (root / request_schema).is_file()
        assert (root / response_schema).is_file()
        registry.validate_instance(request_schema, _request(capability_id))
        registry.validate_instance(
            response_schema, _response(capability_id, data[capability_id])
        )


def test_schemas_reject_unknown_parameters_and_numeric_money() -> None:
    registry = load_registry()
    invalid_request = _request("report.inventory_valuation", {"extra": True})
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(
            "schemas/v1/report.inventory_valuation.request.schema.json",
            invalid_request,
        )

    data = {
        "items": [_cogs(92, "2025-01-31", balance=25.5)],
        "has_more": False,
        "next_cursor": None,
    }
    with pytest.raises(InstanceValidationError):
        registry.validate_instance(
            "schemas/v1/cogs.entries.list.response.schema.json",
            _response("cogs.entries.list", data),
        )
