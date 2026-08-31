from __future__ import annotations

import io
import json

import pytest

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


def _journal() -> dict:
    return {"id": 4, "code": "MISC", "name": "Miscellaneous"}


def _currency() -> dict:
    return {"id": 6, "code": "CNY"}


def _search_item() -> dict:
    return {
        "id": 30,
        "name": "MISC/2025/0030",
        "date": "2025-02-01",
        "state": "posted",
        "ref": None,
        "journal": _journal(),
        "company_id": 7,
        "currency": _currency(),
        "partner": None,
        "debit": "123.45",
        "credit": "123.45",
        "balance": "0",
    }


def _entry() -> dict:
    item = _search_item()
    for key in ("debit", "credit", "balance"):
        item.pop(key)
    item["lines"] = [
        {
            "id": 301,
            "sequence": 10,
            "display_type": "product",
            "name": "Debit",
            "account": {"id": 101, "code": "1000", "name": "Cash"},
            "partner": None,
            "debit": "123.45",
            "credit": "0",
            "balance": "123.45",
            "company_currency": _currency(),
            "amount_currency": "123.45",
            "currency": _currency(),
            "date_maturity": None,
            "reconciled": False,
            "matching_number": None,
            "analytic_distribution": {"3,1": "100"},
        },
        {
            "id": 302,
            "sequence": 20,
            "display_type": "product",
            "name": "Credit",
            "account": {"id": 102, "code": "2000", "name": "Clearing"},
            "partner": None,
            "debit": "0",
            "credit": "123.45",
            "balance": "-123.45",
            "company_currency": _currency(),
            "amount_currency": "-123.45",
            "currency": _currency(),
            "date_maturity": None,
            "reconciled": False,
            "matching_number": None,
            "analytic_distribution": {},
        },
    ]
    item["totals"] = {"debit": "123.45", "credit": "123.45", "balance": "0"}
    return item


def _request(parameters: dict) -> dict:
    return {
        "schema_version": "v1",
        "request_id": "7bc39413-0d69-4092-9319-795d33f3167c",
        "context": _context(),
        "parameters": parameters,
    }


@pytest.mark.parametrize(
    ("capability_id", "parameters", "data"),
    [
        (
            "journal_entry.search",
            {"limit": 1, "states": ["posted"]},
            {"items": [_search_item()], "has_more": False, "next_cursor": None},
        ),
        ("journal_entry.get", {"entry_id": 30}, _entry()),
    ],
)
def test_cli_dispatches_fixed_journal_entry_reads(
    capability_id: str, parameters: dict, data: dict
) -> None:
    class Port:
        user_id = 42

        def search_page(self, **kwargs):
            assert kwargs["company_id"] == 7
            assert kwargs["limit"] == 2
            assert kwargs["filters"]["states"] == ["posted"]
            return {
                "user_id": 42,
                "company_visible": True,
                "module_installed": True,
                "access_allowed": True,
                "rows": [_search_item()],
            }

        def get_entry(self, **kwargs):
            assert kwargs == {"company_id": 7, "entry_id": 30}
            return {
                "user_id": 42,
                "company_visible": True,
                "module_installed": True,
                "access_allowed": True,
                "entry": _entry(),
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
    assert document["data"] == data
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
