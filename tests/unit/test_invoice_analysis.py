from __future__ import annotations

from copy import deepcopy

import pytest

from odoo_accounting_cli_v4.capabilities.invoice_analysis import (
    InvoiceAnalysisError,
    read_invoice_analysis,
    validate_invoice_analysis_request,
)

REQUEST_ID = "7bc39413-0d69-4092-9319-795d33f3167c"


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


def _row(row_id: int, *, partner_id: int = 31) -> dict:
    return {
        "id": row_id,
        "invoice": {"id": 101, "name": "INV/2026/0001"},
        "journal": {"id": 11, "name": "Customer Invoices"},
        "company_id": 7,
        "company_currency": {"id": 6, "code": "CNY"},
        "partner": {"id": partner_id, "name": "Acme"},
        "move_type": "out_invoice",
        "state": "posted",
        "payment_state": "not_paid",
        "invoice_date": "2026-08-20",
        "due_date": "2026-09-20",
        "product": {"id": 41, "name": "Service"},
        "uom": {"id": 1, "name": "Units"},
        "currency": {"id": 6, "code": "CNY"},
        "quantity": "2",
        "untaxed_amount_currency": "100",
        "untaxed_amount": "100",
        "total_amount": "106",
        "total_amount_currency": "106",
        "average_price": "50",
        "margin": "60",
        "inventory_value": "40",
    }


def _summary() -> dict:
    return {
        "group_by": "partner",
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
        "company_id": 7,
        "company_currency": {"id": 6, "code": "CNY"},
        "groups": [
            {
                "group": {"id": 31, "value": "Acme"},
                "row_count": 2,
                "quantity": "3",
                "untaxed_amount": "150",
                "total_amount": "159",
                "margin": "90",
                "inventory_value": "60",
            },
            {
                "group": {"id": 32, "value": "Beta"},
                "row_count": 1,
                "quantity": "1",
                "untaxed_amount": "50",
                "total_amount": "53",
                "margin": "30",
                "inventory_value": "20",
            },
        ],
        "totals": {
            "row_count": 3,
            "quantity": "4",
            "untaxed_amount": "200",
            "total_amount": "212",
            "margin": "120",
            "inventory_value": "80",
        },
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


def test_search_defaults_are_closed_and_dates_are_paired() -> None:
    _, _, parameters = validate_invoice_analysis_request(
        "invoice.analysis.search", _request({})
    )
    assert parameters == {
        "date_from": None,
        "date_to": None,
        "move_types": None,
        "states": None,
        "payment_states": None,
        "partner_id": None,
        "product_id": None,
        "limit": 100,
        "cursor": None,
    }

    for invalid in (
        {"date_from": "2026-01-01"},
        {"date_to": "2026-12-31"},
        {"date_from": "2026-12-31", "date_to": "2026-01-01"},
    ):
        with pytest.raises(InvoiceAnalysisError) as caught:
            validate_invoice_analysis_request(
                "invoice.analysis.search", _request(invalid)
            )
        assert caught.value.code == "invalid_request"


@pytest.mark.parametrize(
    "parameters",
    [
        {"move_types": []},
        {"move_types": ["entry"]},
        {"states": ["posted", "posted"]},
        {"payment_states": ["overdue"]},
        {"partner_id": True},
        {"product_id": 0},
        {"limit": 1001},
        {"extra": True},
    ],
)
def test_search_rejects_expanded_or_invalid_filters(parameters: dict) -> None:
    with pytest.raises(InvoiceAnalysisError) as caught:
        validate_invoice_analysis_request(
            "invoice.analysis.search", _request(parameters)
        )
    assert caught.value.code == "invalid_request"


def test_summary_requires_dates_and_one_allowlisted_group() -> None:
    _, _, parameters = validate_invoice_analysis_request(
        "invoice.analysis.summary",
        _request(
            {
                "date_from": "2026-01-01",
                "date_to": "2026-12-31",
                "group_by": "partner",
            }
        ),
    )
    assert parameters["group_by"] == "partner"
    assert parameters["move_types"] is None

    for invalid in (
        {"group_by": "partner"},
        {
            "date_from": "2026-01-01",
            "date_to": "2026-12-31",
            "group_by": "month",
        },
        {
            "date_from": "2026-01-01",
            "date_to": "2026-12-31",
            "group_by": "partner",
            "limit": 10,
        },
    ):
        with pytest.raises(InvoiceAnalysisError):
            validate_invoice_analysis_request(
                "invoice.analysis.summary", _request(invalid)
            )


def test_search_uses_bound_id_cursor_and_limit_plus_one() -> None:
    first_port = FakePort([_row(30), _row(29)])
    first = read_invoice_analysis(
        first_port,
        "invoice.analysis.search",
        _request({"states": ["posted"], "limit": 1}),
    )
    assert first["items"] == [_row(30)]
    assert first["has_more"] is True
    assert isinstance(first["next_cursor"], str)
    assert first_port.calls[0]["parameters"] == {
        "date_from": None,
        "date_to": None,
        "move_types": None,
        "states": ["posted"],
        "payment_states": None,
        "partner_id": None,
        "product_id": None,
        "limit": 2,
        "after": None,
    }

    second_port = FakePort([_row(29)])
    second = read_invoice_analysis(
        second_port,
        "invoice.analysis.search",
        _request(
            {
                "states": ["posted"],
                "limit": 1,
                "cursor": first["next_cursor"],
            }
        ),
    )
    assert second == {"items": [_row(29)], "has_more": False, "next_cursor": None}
    assert second_port.calls[0]["parameters"]["after"] == 30


def test_cursor_is_bound_to_filters_company_database_and_user() -> None:
    first = read_invoice_analysis(
        FakePort([_row(30), _row(29)]),
        "invoice.analysis.search",
        _request({"limit": 1}),
    )
    with pytest.raises(InvoiceAnalysisError) as caught:
        read_invoice_analysis(
            FakePort([]),
            "invoice.analysis.search",
            _request({"limit": 1, "partner_id": 31, "cursor": first["next_cursor"]}),
        )
    assert caught.value.code == "invalid_cursor"


def test_summary_validates_groups_and_exact_totals() -> None:
    summary = _summary()
    port = FakePort([summary])
    result = read_invoice_analysis(
        port,
        "invoice.analysis.summary",
        _request(
            {
                "date_from": "2026-01-01",
                "date_to": "2026-12-31",
                "group_by": "partner",
            }
        ),
    )
    assert result == summary
    assert "after" not in port.calls[0]["parameters"]

    bad = _summary()
    bad["totals"]["total_amount"] = "211"
    with pytest.raises(InvoiceAnalysisError) as caught:
        read_invoice_analysis(
            FakePort([bad]),
            "invoice.analysis.summary",
            _request(
                {
                    "date_from": "2026-01-01",
                    "date_to": "2026-12-31",
                    "group_by": "partner",
                }
            ),
        )
    assert caught.value.code == "failed_validation"


@pytest.mark.parametrize(
    ("flags", "code"),
    [
        ({"company_visible": False}, "company_unavailable"),
        ({"module_installed": False}, "uninstalled"),
        ({"access_allowed": False}, "unauthorized"),
        ({"cursor_found": False}, "invalid_cursor"),
    ],
)
def test_runtime_scope_failures_are_fail_closed(flags: dict, code: str) -> None:
    with pytest.raises(InvoiceAnalysisError) as caught:
        read_invoice_analysis(
            FakePort([], **flags), "invoice.analysis.search", _request({})
        )
    assert caught.value.code == code


def test_search_rejects_cross_company_nonfinite_and_bad_order() -> None:
    for rows in (
        [{**_row(30), "company_id": 8}],
        [{**_row(30), "total_amount": "NaN"}],
        [_row(29), _row(30)],
    ):
        with pytest.raises(InvoiceAnalysisError) as caught:
            read_invoice_analysis(
                FakePort(rows), "invoice.analysis.search", _request({})
            )
        assert caught.value.code == "failed_validation"
