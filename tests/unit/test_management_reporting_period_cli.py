from __future__ import annotations

import io
import json

import pytest

from odoo_accounting_cli_v4.cli import main


def _request(parameters: dict) -> dict:
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


def _run(capability_id: str, parameters: dict, port: object) -> dict:
    stdout = io.StringIO()
    stderr = io.StringIO()
    exit_code = main(
        ["read", capability_id, "--request", "-"],
        stdin=io.StringIO(json.dumps(_request(parameters))),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda selected, parsed: port,
    )
    assert exit_code == 0
    assert stderr.getvalue() == ""
    return json.loads(stdout.getvalue())


class _PeriodPort:
    user_id = 42

    def read(self, *, capability_id, company_id, parameters):
        assert company_id == 7
        item = {
            "id": 19,
            "name": "FY 2025",
            "company_id": 7,
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        }
        if capability_id == "company.lock_dates.inspect":
            assert parameters == {}
            data = {
                "company_id": 7,
                "configured": {
                    "fiscalyear_lock_date": None,
                    "tax_lock_date": None,
                    "sale_lock_date": None,
                    "purchase_lock_date": None,
                    "hard_lock_date": None,
                },
                "effective": {
                    "fiscalyear_lock_date": None,
                    "tax_lock_date": None,
                    "sale_lock_date": None,
                    "purchase_lock_date": None,
                    "hard_lock_date": None,
                },
            }
        elif capability_id == "company.fiscal_year.resolve":
            assert parameters == {"date": "2025-06-30"}
            data = {
                "company_id": 7,
                "date": "2025-06-30",
                "date_from": "2025-01-01",
                "date_to": "2025-12-31",
                "fiscal_year": {"id": 19, "name": "FY 2025"},
            }
        else:
            data = item
        return {
            "user_id": 42,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "cursor_found": True,
            "items": [data],
        }


@pytest.mark.parametrize(
    ("capability_id", "parameters", "record_ids"),
    [
        ("company.lock_dates.inspect", {}, [7]),
        ("company.fiscal_year.resolve", {"date": "2025-06-30"}, [7]),
        (
            "fiscal_year.search",
            {"contains_date": "2025-06-30", "limit": 10},
            [19],
        ),
        ("fiscal_year.get", {"fiscal_year_id": 19}, [19]),
    ],
)
def test_cli_dispatches_period_context_reads(
    capability_id: str, parameters: dict, record_ids: list[int]
) -> None:
    document = _run(capability_id, parameters, _PeriodPort())

    assert document["capability"] == capability_id
    assert document["odoo"]["record_ids"] == record_ids


class _InvoiceAnalysisPort:
    user_id = 42

    def read(self, *, capability_id, company_id, parameters):
        assert company_id == 7
        if capability_id == "invoice.analysis.search":
            item = {
                "id": 31,
                "invoice": {"id": 11, "name": "INV/2025/001"},
                "journal": {"id": 2, "name": "Customer Invoices"},
                "company_id": 7,
                "company_currency": {"id": 6, "code": "CNY"},
                "partner": {"id": 16, "name": "Customer"},
                "move_type": "out_invoice",
                "state": "posted",
                "payment_state": "not_paid",
                "invoice_date": "2025-01-10",
                "due_date": "2025-02-10",
                "product": {"id": 4, "name": "Service"},
                "uom": {"id": 1, "name": "Units"},
                "currency": {"id": 6, "code": "CNY"},
                "quantity": "1",
                "untaxed_amount_currency": "100",
                "untaxed_amount": "100",
                "total_amount": "106",
                "total_amount_currency": "106",
                "average_price": "100",
                "margin": "20",
                "inventory_value": "80",
            }
        else:
            item = {
                "group_by": "move_type",
                "date_from": "2025-01-01",
                "date_to": "2025-12-31",
                "company_id": 7,
                "company_currency": {"id": 6, "code": "CNY"},
                "groups": [
                    {
                        "group": {"id": None, "value": "out_invoice"},
                        "row_count": 1,
                        "quantity": "1",
                        "untaxed_amount": "100",
                        "total_amount": "106",
                        "margin": "20",
                        "inventory_value": "80",
                    }
                ],
                "totals": {
                    "row_count": 1,
                    "quantity": "1",
                    "untaxed_amount": "100",
                    "total_amount": "106",
                    "margin": "20",
                    "inventory_value": "80",
                },
            }
        return {
            "user_id": 42,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "cursor_found": True,
            "items": [item],
        }


@pytest.mark.parametrize(
    ("capability_id", "parameters", "record_ids"),
    [
        (
            "invoice.analysis.search",
            {"date_from": "2025-01-01", "date_to": "2025-12-31"},
            [31],
        ),
        (
            "invoice.analysis.summary",
            {
                "date_from": "2025-01-01",
                "date_to": "2025-12-31",
                "group_by": "move_type",
            },
            [],
        ),
    ],
)
def test_cli_dispatches_invoice_analysis_reads(
    capability_id: str, parameters: dict, record_ids: list[int]
) -> None:
    document = _run(capability_id, parameters, _InvoiceAnalysisPort())

    assert document["capability"] == capability_id
    assert document["odoo"]["record_ids"] == record_ids
