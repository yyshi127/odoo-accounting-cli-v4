from __future__ import annotations

from copy import deepcopy

import pytest

from odoo_accounting_cli_v4.capabilities.order_documents import (
    OrderDocumentReadError,
    read_order_document,
    validate_order_document_request,
)

REQUEST_ID = "68c7fc48-53bd-4711-b1e0-ec0e73b296a4"


def _request(parameters: dict, *, company_id: int = 7) -> dict:
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "context": {
            "database": "odoo_cli_v4_dev",
            "company_id": company_id,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": deepcopy(parameters),
    }


def _ref(record_id: int, name: str) -> dict:
    return {"id": record_id, "name": name}


def _currency(record_id: int = 6, code: str = "CNY") -> dict:
    return {"id": record_id, "code": code}


def _sale_line(line_id: int = 100) -> dict:
    return {
        "id": line_id,
        "order": _ref(10, "S00010"),
        "company": _ref(7, "China Company"),
        "partner": _ref(31, "Customer"),
        "state": "draft",
        "date_order": "2026-08-28T01:02:03Z",
        "sequence": 10,
        "display_type": None,
        "description": "Test product",
        "product": _ref(41, "Test product"),
        "uom": _ref(1, "Units"),
        "ordered_quantity": "3",
        "invoiced_quantity": "0",
        "to_invoice_quantity": "3",
        "unit_price": "10",
        "discount_percent": "0",
        "amount_untaxed": "30",
        "amount_tax": "0",
        "amount_total": "30",
        "currency": _currency(),
        "taxes": [],
        "invoice_line_ids": [],
        "stock_move_ids": [],
        "delivered_quantity": "0",
        "to_deliver_quantity": "3",
    }


def _purchase_line(line_id: int = 200) -> dict:
    return {
        "id": line_id,
        "order": _ref(20, "P00020"),
        "company": _ref(7, "China Company"),
        "partner": _ref(32, "Vendor"),
        "state": "draft",
        "date_order": "2026-08-28T01:02:03Z",
        "sequence": 10,
        "display_type": None,
        "description": "Test product",
        "product": _ref(41, "Test product"),
        "uom": _ref(1, "Units"),
        "ordered_quantity": "5",
        "invoiced_quantity": "0",
        "to_invoice_quantity": "5",
        "unit_price": "8",
        "discount_percent": "0",
        "amount_untaxed": "40",
        "amount_tax": "0",
        "amount_total": "40",
        "currency": _currency(),
        "taxes": [],
        "invoice_line_ids": [],
        "stock_move_ids": [],
        "received_quantity": "0",
        "to_receive_quantity": "5",
        "date_planned": "2026-08-29T01:02:03Z",
    }


def _sale_header(order_id: int = 10, *, include_details: bool = False) -> dict:
    value = {
        "id": order_id,
        "name": f"S{order_id:05d}",
        "company": _ref(7, "China Company"),
        "partner": _ref(31, "Customer"),
        "state": "draft",
        "date_order": "2026-08-28T01:02:03Z",
        "currency": _currency(),
        "user": _ref(5, "Accountant"),
        "invoice_status": "to invoice",
        "amount_untaxed": "30",
        "amount_tax": "0",
        "amount_total": "30",
        "invoice_ids": [],
        "transfer_ids": [],
        "line_count": 1,
        "validity_date": "2026-09-27",
        "client_order_ref": "CLIENT-1",
        "team": None,
        "delivery_status": None,
    }
    if include_details:
        value.update(lines=[_sale_line()], invoices=[], transfers=[])
    return value


def _purchase_header(order_id: int = 20, *, include_details: bool = False) -> dict:
    value = {
        "id": order_id,
        "name": f"P{order_id:05d}",
        "company": _ref(7, "China Company"),
        "partner": _ref(32, "Vendor"),
        "state": "draft",
        "date_order": "2026-08-28T01:02:03Z",
        "currency": _currency(),
        "user": _ref(5, "Accountant"),
        "invoice_status": "to invoice",
        "amount_untaxed": "40",
        "amount_tax": "0",
        "amount_total": "40",
        "invoice_ids": [],
        "transfer_ids": [],
        "line_count": 1,
        "date_approve": None,
        "partner_ref": "VENDOR-1",
        "origin": None,
        "receipt_status": None,
    }
    if include_details:
        value.update(lines=[_purchase_line()], invoices=[], transfers=[])
    return value


def _summary() -> dict:
    return {
        "company_id": 7,
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
        "group_by": "partner",
        "groups": [
            {
                "group": {"id": 31, "value": "Customer"},
                "currency": _currency(),
                "order_count": 1,
                "amount_untaxed": "30",
                "amount_tax": "0",
                "amount_total": "30",
            },
            {
                "group": {"id": 31, "value": "Customer"},
                "currency": _currency(2, "USD"),
                "order_count": 1,
                "amount_untaxed": "20",
                "amount_tax": "0",
                "amount_total": "20",
            },
        ],
        "totals_by_currency": [
            {
                "currency": _currency(2, "USD"),
                "order_count": 1,
                "amount_untaxed": "20",
                "amount_tax": "0",
                "amount_total": "20",
            },
            {
                "currency": _currency(),
                "order_count": 1,
                "amount_untaxed": "30",
                "amount_tax": "0",
                "amount_total": "30",
            },
        ],
    }


class FakePort:
    user_id = 5

    def __init__(self, items: list[dict], **flags: bool) -> None:
        self.items = deepcopy(items)
        self.flags = flags
        self.calls: list[dict] = []

    def read(self, *, capability_id: str, company_id: int, parameters: dict) -> dict:
        self.calls.append(
            {
                "capability_id": capability_id,
                "company_id": company_id,
                "parameters": deepcopy(parameters),
            }
        )
        return {
            "user_id": self.user_id,
            "company_visible": self.flags.get("company_visible", True),
            "module_installed": self.flags.get("module_installed", True),
            "access_allowed": self.flags.get("access_allowed", True),
            "cursor_found": self.flags.get("cursor_found", True),
            "items": deepcopy(self.items),
        }


@pytest.mark.parametrize("prefix", ["sale", "purchase"])
def test_search_defaults_are_closed_and_dates_are_independent_bounds(
    prefix: str,
) -> None:
    _, _, parameters = validate_order_document_request(
        f"{prefix}.order.search", _request({})
    )
    assert parameters == {
        "query": None,
        "date_from": None,
        "date_to": None,
        "states": None,
        "partner_id": None,
        "currency_id": None,
        "invoice_statuses": None,
        "limit": 100,
        "cursor": None,
    }

    for valid in ({"date_from": "2026-01-01"}, {"date_to": "2026-12-31"}):
        _, _, normalized = validate_order_document_request(
            f"{prefix}.order.search", _request(valid)
        )
        assert all(normalized[key] == value for key, value in valid.items())

    for invalid in (
        {"date_from": "2026-12-31", "date_to": "2026-01-01"},
        {"domain": []},
    ):
        with pytest.raises(OrderDocumentReadError) as caught:
            validate_order_document_request(f"{prefix}.order.search", _request(invalid))
        assert caught.value.code == "invalid_request"


@pytest.mark.parametrize("prefix", ["sale", "purchase"])
def test_get_and_summary_contracts_are_closed(prefix: str) -> None:
    _, _, get_parameters = validate_order_document_request(
        f"{prefix}.order.get", _request({"order_id": 10})
    )
    assert get_parameters == {"order_id": 10}

    _, _, summary_parameters = validate_order_document_request(
        f"{prefix}.order.analysis.summary",
        _request(
            {
                "date_from": "2026-01-01",
                "date_to": "2026-12-31",
                "group_by": "partner",
            }
        ),
    )
    assert summary_parameters == {
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
        "group_by": "partner",
        "states": None,
        "partner_id": None,
        "currency_id": None,
    }

    for invalid in (
        {"date_from": "2026-01-01", "date_to": "2026-12-31"},
        {"date_from": "2026-01-01", "date_to": "2026-12-31", "group_by": "month"},
    ):
        with pytest.raises(OrderDocumentReadError):
            validate_order_document_request(
                f"{prefix}.order.analysis.summary", _request(invalid)
            )


@pytest.mark.parametrize(
    ("capability_id", "flag"),
    [
        ("sale.order.line.search", "to_deliver_only"),
        ("purchase.order.line.search", "to_receive_only"),
    ],
)
def test_line_search_normalizes_only_the_document_specific_pending_flag(
    capability_id: str, flag: str
) -> None:
    _, _, parameters = validate_order_document_request(
        capability_id, _request({"order_id": 10, flag: True})
    )
    assert parameters == {
        "order_id": 10,
        "date_from": None,
        "date_to": None,
        "partner_id": None,
        "product_id": None,
        "states": None,
        flag: True,
        "to_invoice_only": False,
        "limit": 100,
        "cursor": None,
    }


def test_search_uses_bound_ascending_id_cursor_and_limit_plus_one() -> None:
    first_port = FakePort([_sale_header(10), _sale_header(11)])
    first = read_order_document(
        first_port,
        "sale.order.search",
        _request({"states": ["draft"], "limit": 1}),
    )
    assert first["items"] == [_sale_header(10)]
    assert first["has_more"] is True
    assert isinstance(first["next_cursor"], str)
    assert first_port.calls[0]["parameters"] == {
        "query": None,
        "date_from": None,
        "date_to": None,
        "states": ["draft"],
        "partner_id": None,
        "currency_id": None,
        "invoice_statuses": None,
        "limit": 2,
        "after": None,
    }

    second_port = FakePort([_sale_header(11)])
    second = read_order_document(
        second_port,
        "sale.order.search",
        _request(
            {
                "states": ["draft"],
                "limit": 1,
                "cursor": first["next_cursor"],
            }
        ),
    )
    assert second == {
        "items": [_sale_header(11)],
        "has_more": False,
        "next_cursor": None,
    }
    assert second_port.calls[0]["parameters"]["after"] == 10


def test_get_lines_and_summary_validate_exact_document_shapes() -> None:
    assert read_order_document(
        FakePort([_sale_header(include_details=True)]),
        "sale.order.get",
        _request({"order_id": 10}),
    ) == _sale_header(include_details=True)
    assert read_order_document(
        FakePort([_purchase_line()]),
        "purchase.order.line.search",
        _request({"order_id": 20}),
    )["items"] == [_purchase_line()]
    assert (
        read_order_document(
            FakePort([_summary()]),
            "sale.order.analysis.summary",
            _request(
                {
                    "date_from": "2026-01-01",
                    "date_to": "2026-12-31",
                    "group_by": "partner",
                }
            ),
        )
        == _summary()
    )


def test_summary_rejects_cross_currency_totals_and_rows_are_ascending() -> None:
    bad_summary = _summary()
    bad_summary["totals_by_currency"] = [
        {
            "currency": _currency(),
            "order_count": 2,
            "amount_untaxed": "50",
            "amount_tax": "0",
            "amount_total": "50",
        }
    ]
    for capability_id, parameters, rows in (
        (
            "sale.order.analysis.summary",
            {"date_from": "2026-01-01", "date_to": "2026-12-31", "group_by": "partner"},
            [bad_summary],
        ),
        ("sale.order.search", {}, [_sale_header(11), _sale_header(10)]),
    ):
        with pytest.raises(OrderDocumentReadError) as caught:
            read_order_document(FakePort(rows), capability_id, _request(parameters))
        assert caught.value.code == "failed_validation"


@pytest.mark.parametrize(
    ("flags", "code"),
    [
        (
            {"company_visible": False, "access_allowed": False},
            "company_unavailable",
        ),
        ({"module_installed": False, "access_allowed": False}, "uninstalled"),
        ({"access_allowed": False}, "unauthorized"),
        ({"cursor_found": False}, "failed_validation"),
    ],
)
def test_runtime_scope_failures_are_fail_closed(flags: dict, code: str) -> None:
    with pytest.raises(OrderDocumentReadError) as caught:
        read_order_document(FakePort([], **flags), "sale.order.search", _request({}))
    assert caught.value.code == code


def test_runtime_missing_bound_cursor_is_invalid_cursor() -> None:
    first = read_order_document(
        FakePort([_sale_header(10), _sale_header(11)]),
        "sale.order.search",
        _request({"limit": 1}),
    )
    with pytest.raises(OrderDocumentReadError) as caught:
        read_order_document(
            FakePort([], cursor_found=False),
            "sale.order.search",
            _request({"limit": 1, "cursor": first["next_cursor"]}),
        )
    assert caught.value.code == "invalid_cursor"


def test_response_rejects_cross_company_numeric_amount_and_expanded_shape() -> None:
    for row in (
        {**_sale_header(), "company": _ref(8, "Other")},
        {**_sale_header(), "amount_total": 30},
        {**_purchase_line(), "product_uom": _ref(1, "Wrong Odoo 19 field")},
    ):
        capability_id = (
            "purchase.order.line.search"
            if "product_uom" in row
            else "sale.order.search"
        )
        with pytest.raises(OrderDocumentReadError) as caught:
            read_order_document(FakePort([row]), capability_id, _request({}))
        assert caught.value.code == "failed_validation"
