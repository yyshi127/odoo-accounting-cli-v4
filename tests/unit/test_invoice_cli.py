from __future__ import annotations

import io
import json

import pytest

from odoo_accounting_cli_v4.bridge.invoices import OdooInvoicePort
from odoo_accounting_cli_v4.cli import main
from odoo_accounting_cli_v4.registry import load_registry


def _context() -> dict:
    return {
        "database": "v4-dev",
        "company_id": 7,
        "user_login": "v4-agent",
        "language": "en_US",
        "timezone": "Asia/Shanghai",
    }


def _request(parameters: dict) -> dict:
    return {
        "schema_version": "v1",
        "request_id": "7bc39413-0d69-4092-9319-795d33f3167c",
        "context": _context(),
        "parameters": parameters,
    }


def _header() -> dict:
    return {
        "id": 30,
        "name": "INV/2025/0030",
        "move_type": "out_invoice",
        "state": "posted",
        "date": "2025-01-20",
        "invoice_date": "2025-01-20",
        "invoice_date_due": "2025-02-20",
        "ref": None,
        "payment_reference": None,
        "invoice_origin": None,
        "journal": {"id": 8, "code": "INV", "name": "Customer Invoices"},
        "company_id": 7,
        "currency": {"id": 6, "code": "CNY"},
        "partner": {"id": 9, "name": "Fixture Customer"},
        "amount_untaxed": "100",
        "amount_tax": "13",
        "amount_total": "113",
        "amount_residual": "63",
        "payment_state": "partial",
    }


def _payment_status() -> dict:
    return {
        "id": 30,
        "name": "INV/2025/0030",
        "move_type": "out_invoice",
        "state": "posted",
        "payment_state": "partial",
        "company_id": 7,
        "currency": {"id": 6, "code": "CNY"},
        "company_currency": {"id": 6, "code": "CNY"},
        "amount_total": "113",
        "amount_residual": "63",
        "receivable_payable_lines": [],
        "reconciliations": [],
        "payments": [],
    }


@pytest.mark.parametrize(
    ("capability_id", "parameters", "expected_data"),
    (
        (
            "invoice.search",
            {"limit": 1},
            {"items": [_header()], "has_more": False, "next_cursor": None},
        ),
        ("invoice.get", {"invoice_id": 30}, {**_header(), "lines": []}),
        (
            "invoice.payment_status.inspect",
            {"invoice_id": 30},
            _payment_status(),
        ),
    ),
)
def test_cli_dispatches_fixed_invoice_reads(
    capability_id: str, parameters: dict, expected_data: dict
) -> None:
    class Port:
        user_id = 42

        def search_page(self, **kwargs):
            assert kwargs["company_id"] == 7
            assert kwargs["limit"] == 2
            assert kwargs["after"] is None
            return {
                "user_id": 42,
                "company_visible": True,
                "module_installed": True,
                "access_allowed": True,
                "rows": [_header()],
            }

        def get_invoice(self, **kwargs):
            assert kwargs == {"company_id": 7, "invoice_id": 30}
            return {
                "user_id": 42,
                "company_visible": True,
                "module_installed": True,
                "access_allowed": True,
                "invoice": {**_header(), "lines": []},
            }

        def inspect_payment_status(self, **kwargs):
            assert kwargs == {"company_id": 7, "invoice_id": 30}
            return {
                "user_id": 42,
                "company_visible": True,
                "module_installed": True,
                "access_allowed": True,
                "payment_status": _payment_status(),
            }

    stdout = io.StringIO()
    stderr = io.StringIO()
    result = main(
        ["read", capability_id, "--request", "-"],
        stdin=io.StringIO(json.dumps(_request(parameters))),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda selected, request: Port(),
    )

    document = json.loads(stdout.getvalue())
    assert result == 0
    assert stderr.getvalue() == ""
    assert document["success"] is True
    assert document["data"] == expected_data
    assert document["odoo"] == {
        "database": "v4-dev",
        "company_id": 7,
        "user_id": 42,
        "model": "account.move",
        "record_ids": [30],
    }
    load_registry().validate_instance(
        f"schemas/v1/{capability_id}.response.schema.json", document
    )


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    [
        ("invoice.get", {"invoice_id": 30}),
        ("invoice.payment_status.inspect", {"invoice_id": 30}),
    ],
)
def test_invoice_not_found_preserves_verified_odoo_context(
    capability_id: str, parameters: dict
) -> None:
    class Port:
        user_id = 42

        def get_invoice(self, **kwargs):
            return {
                "user_id": 42,
                "company_visible": True,
                "module_installed": True,
                "access_allowed": True,
                "invoice": None,
            }

        def inspect_payment_status(self, **kwargs):
            return {
                "user_id": 42,
                "company_visible": True,
                "module_installed": True,
                "access_allowed": True,
                "payment_status": None,
            }

    stdout = io.StringIO()
    stderr = io.StringIO()
    result = main(
        ["read", capability_id, "--request", "-"],
        stdin=io.StringIO(json.dumps(_request(parameters))),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda selected, request: Port(),
    )

    document = json.loads(stdout.getvalue())
    assert result == 4
    assert stderr.getvalue() == ""
    assert document["error"]["code"] == "record_not_found"
    assert document["odoo"] == {
        "database": "v4-dev",
        "company_id": 7,
        "user_id": 42,
        "model": "account.move",
        "record_ids": [],
    }
    load_registry().validate_instance(
        f"schemas/v1/{capability_id}.response.schema.json", document
    )


def test_invalid_cursor_does_not_require_unverified_odoo_context() -> None:
    class Client:
        def invoke(self, action, payload):
            raise AssertionError("invalid cursor must fail before bridge invocation")

    stdout = io.StringIO()
    stderr = io.StringIO()
    result = main(
        ["read", "invoice.search", "--request", "-"],
        stdin=io.StringIO(
            json.dumps(_request({"limit": 1, "cursor": "not-a-valid-cursor"}))
        ),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda selected, request: OdooInvoicePort(Client()),
    )

    document = json.loads(stdout.getvalue())
    assert result == 2
    assert stderr.getvalue() == ""
    assert document["request_id"] == _request({})["request_id"]
    assert document["error"]["code"] == "invalid_cursor"
    assert document["odoo"] == {
        "database": None,
        "company_id": None,
        "user_id": None,
        "model": None,
        "record_ids": [],
    }
    load_registry().validate_instance(
        "schemas/v1/invoice.search.response.schema.json", document
    )
