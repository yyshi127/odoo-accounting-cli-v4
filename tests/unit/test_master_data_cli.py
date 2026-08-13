from __future__ import annotations

import io
import json

import pytest

from odoo_accounting_cli_v4.cli import main
from odoo_accounting_cli_v4.registry import load_registry


CASES = {
    "company.accounting_context.list": (
        "res.company",
        {
            "id": 7,
            "name": "China Company",
            "sequence": 0,
            "active": True,
            "current": True,
            "currency": {"id": 6, "code": "CNY", "decimal_places": 2},
            "country": {"id": 48, "code": "CN", "name": "China"},
            "fiscal_country": {"id": 48, "code": "CN", "name": "China"},
            "chart_template": "cn_oscg",
            "tax_calculation_rounding_method": "round_globally",
            "fiscal_year_end": {"month": 12, "day": 31},
        },
    ),
    "journal.list": (
        "account.journal",
        {
            "id": 9,
            "sequence": 5,
            "code": "INV",
            "name": "Sales",
            "type": "sale",
            "active": True,
            "currency": None,
            "company_id": 7,
        },
    ),
    "tax.list": (
        "account.tax",
        {
            "id": 5,
            "sequence": 1,
            "name": "13% INC",
            "type_tax_use": "sale",
            "amount_type": "percent",
            "amount": "13",
            "price_include": False,
            "include_base_amount": False,
            "is_base_affected": True,
            "active": True,
            "tax_group": {"id": 5, "name": "VAT 13%"},
            "company_id": 7,
        },
    ),
    "payment_term.list": (
        "account.payment.term",
        {
            "id": 1,
            "sequence": 10,
            "name": "Immediate Payment",
            "active": True,
            "company_id": None,
            "display_on_invoice": True,
            "early_discount": False,
            "discount_percentage": "2",
            "discount_days": 10,
            "early_pay_discount_computation": "included",
            "lines": [
                {
                    "id": 1,
                    "value": "percent",
                    "value_amount": "100",
                    "delay_type": "days_after",
                    "nb_days": 0,
                    "days_next_month": "10",
                }
            ],
        },
    ),
    "currency.list": (
        "res.currency",
        {
            "id": 6,
            "code": "CNY",
            "name": "Chinese yuan",
            "symbol": "¥",
            "rounding": "0.01",
            "decimal_places": 2,
            "active": True,
            "position": "before",
            "is_company_currency": True,
        },
    ),
}


def _request() -> dict:
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
        "parameters": {"limit": 1, "cursor": None},
    }


@pytest.mark.parametrize("capability_id", CASES)
def test_cli_dispatches_each_fixed_master_data_capability(capability_id: str) -> None:
    model, row = CASES[capability_id]

    class Port:
        user_id = 42

        def read_page(self, *, company_id, after, limit):
            assert (company_id, after, limit) == (7, None, 2)
            return {
                "user_id": self.user_id,
                "company_visible": True,
                "module_installed": True,
                "access_allowed": True,
                "rows": [row],
            }

    stdout = io.StringIO()
    stderr = io.StringIO()
    result = main(
        ["read", capability_id, "--request", "-"],
        stdin=io.StringIO(json.dumps(_request())),
        stdout=stdout,
        stderr=stderr,
        port_factory=lambda selected, request: Port(),
    )

    document = json.loads(stdout.getvalue())
    assert result == 0
    assert stderr.getvalue() == ""
    assert document["success"] is True
    assert document["capability"] == capability_id
    assert document["data"] == {
        "items": [row],
        "has_more": False,
        "next_cursor": None,
    }
    assert document["odoo"] == {
        "database": "v4-dev",
        "company_id": 7,
        "user_id": 42,
        "model": model,
        "record_ids": [row["id"]],
    }
    load_registry().validate_instance(
        f"schemas/v1/{capability_id}.response.schema.json", document
    )
