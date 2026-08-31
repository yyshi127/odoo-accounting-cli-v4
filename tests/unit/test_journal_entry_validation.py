from __future__ import annotations

import copy
from pathlib import Path

import pytest

from odoo_accounting_cli_v4.capabilities.journal_entries import (
    JournalEntryError,
    check_journal_entry,
    validate_journal_entry_check_request,
)
from odoo_accounting_cli_v4.registry import load_registry


class FakePort:
    def __init__(
        self,
        *,
        entry: dict | None = None,
        company_visible: bool = True,
        module_installed: bool = True,
        access_allowed: bool | None = None,
    ) -> None:
        self.user_id = 42
        self.entry = copy.deepcopy(entry)
        self.company_visible = company_visible
        self.module_installed = module_installed
        self.access_allowed = (
            company_visible and module_installed
            if access_allowed is None
            else access_allowed
        )
        self.calls: list[dict] = []

    def check_entry(self, **kwargs) -> dict:
        self.calls.append(copy.deepcopy(kwargs))
        return {
            "user_id": self.user_id,
            "company_visible": self.company_visible,
            "module_installed": self.module_installed,
            "access_allowed": self.access_allowed,
            "entry": copy.deepcopy(self.entry),
        }


def _request(entry_id: int = 30) -> dict:
    return {
        "schema_version": "v1",
        "request_id": "7bc39413-0d69-4092-9319-795d33f3167c",
        "context": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "zh_CN",
            "timezone": "Asia/Shanghai",
        },
        "parameters": {"entry_id": entry_id},
    }


def _currency() -> dict:
    return {"id": 6, "code": "CNY"}


def _line(
    line_id: int,
    *,
    debit: str,
    credit: str,
    balance: str,
) -> dict:
    return {
        "id": line_id,
        "sequence": 10,
        "display_type": "product",
        "name": f"Line {line_id}",
        "account": {"id": line_id, "code": str(line_id), "name": "Account"},
        "partner": None,
        "debit": debit,
        "credit": credit,
        "balance": balance,
        "company_currency": _currency(),
        "amount_currency": balance,
        "currency": _currency(),
        "date_maturity": None,
        "reconciled": False,
        "matching_number": None,
        "analytic_distribution": {},
    }


def _entry() -> dict:
    return {
        "id": 30,
        "name": None,
        "date": "2025-02-01",
        "state": "draft",
        "ref": "validation-fixture",
        "journal": {"id": 4, "code": "MISC", "name": "Miscellaneous"},
        "company_id": 7,
        "currency": _currency(),
        "partner": None,
        "lines": [
            _line(301, debit="123.45", credit="0.00", balance="123.45"),
            _line(302, debit="0.00", credit="123.45", balance="-123.45"),
        ],
        "totals": {"debit": "123.45", "credit": "123.45", "balance": "0.00"},
    }


def _expected(entry: dict, *, ready: bool, draft: bool, balanced: bool, lines: bool) -> dict:
    return {
        "entry_id": entry["id"],
        "company_id": entry["company_id"],
        "state": entry["state"],
        "ready": ready,
        "checks": {
            "company_matches": True,
            "state_is_draft": draft,
            "debits_equal_credits": balanced,
            "line_items_valid": lines,
        },
        "line_count": len(entry["lines"]),
        "accountable_line_count": len(
            [
                line
                for line in entry["lines"]
                if line["display_type"]
                not in {"line_section", "line_subsection", "line_note"}
            ]
        ),
        "totals": entry["totals"],
    }


def test_check_reports_a_balanced_draft_entry_as_ready() -> None:
    entry = _entry()
    port = FakePort(entry=entry)

    result = check_journal_entry(port, _request())

    assert result == _expected(
        entry, ready=True, draft=True, balanced=True, lines=True
    )
    assert port.calls == [{"company_id": 7, "entry_id": 30}]


def test_check_reports_state_balance_and_line_failures_without_writing() -> None:
    posted = _entry()
    posted["state"] = "posted"
    assert check_journal_entry(FakePort(entry=posted), _request()) == _expected(
        posted, ready=False, draft=False, balanced=True, lines=True
    )

    unbalanced = _entry()
    unbalanced["lines"][1].update(
        credit="100.00", balance="-100.00", amount_currency="-100.00"
    )
    unbalanced["totals"] = {
        "debit": "123.45",
        "credit": "100.00",
        "balance": "23.45",
    }
    assert check_journal_entry(FakePort(entry=unbalanced), _request()) == _expected(
        unbalanced, ready=False, draft=True, balanced=False, lines=True
    )

    invalid_line = _entry()
    invalid_line["lines"][0].update(
        debit="123.45", credit="1.00", balance="122.45", amount_currency="122.45"
    )
    invalid_line["totals"] = {
        "debit": "123.45",
        "credit": "124.45",
        "balance": "-1.00",
    }
    assert check_journal_entry(FakePort(entry=invalid_line), _request()) == _expected(
        invalid_line, ready=False, draft=True, balanced=False, lines=False
    )


def test_check_requires_two_accountable_lines() -> None:
    entry = _entry()
    entry["lines"] = [entry["lines"][0]]
    entry["totals"] = {
        "debit": "123.45",
        "credit": "0.00",
        "balance": "123.45",
    }

    result = check_journal_entry(FakePort(entry=entry), _request())

    assert result == _expected(
        entry, ready=False, draft=True, balanced=False, lines=False
    )


def test_check_fails_closed_for_missing_or_out_of_scope_entries() -> None:
    with pytest.raises(JournalEntryError) as caught:
        check_journal_entry(FakePort(entry=None), _request())
    assert caught.value.code == "record_not_found"
    assert caught.value.exit_code == 4

    entry = _entry()
    entry["company_id"] = 8
    with pytest.raises(JournalEntryError) as caught:
        check_journal_entry(FakePort(entry=entry), _request())
    assert caught.value.code == "failed_validation"
    assert caught.value.exit_code == 8


@pytest.mark.parametrize(
    ("port", "code"),
    [
        (FakePort(company_visible=False), "company_unavailable"),
        (FakePort(module_installed=False), "uninstalled"),
        (FakePort(access_allowed=False), "unauthorized"),
    ],
)
def test_check_preserves_runtime_availability_errors(
    port: FakePort, code: str
) -> None:
    with pytest.raises(JournalEntryError) as caught:
        check_journal_entry(port, _request())
    assert caught.value.code == code


def test_check_request_is_closed_and_requires_a_positive_non_boolean_id() -> None:
    assert validate_journal_entry_check_request(_request())[2] == 30
    for value in (0, -1, True, "30"):
        with pytest.raises(JournalEntryError) as caught:
            validate_journal_entry_check_request(_request(value))
        assert caught.value.code == "invalid_request"
    request = _request()
    request["parameters"]["unexpected"] = True
    with pytest.raises(JournalEntryError):
        validate_journal_entry_check_request(request)


def test_validation_schemas_accept_success_and_error_documents() -> None:
    schema_dir = Path(__file__).parents[2] / "schemas" / "v1"
    request_schema = "schemas/v1/validation.journal_entry.check.request.schema.json"
    response_schema = "schemas/v1/validation.journal_entry.check.response.schema.json"
    assert (schema_dir / Path(request_schema).name).is_file()
    assert (schema_dir / Path(response_schema).name).is_file()
    data = check_journal_entry(FakePort(entry=_entry()), _request())
    response = {
        "schema_version": "v1",
        "request_id": _request()["request_id"],
        "success": True,
        "capability": "validation.journal_entry.check",
        "status": "verified",
        "data": data,
        "warnings": [],
        "error": None,
        "odoo": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_id": 42,
            "model": "account.move",
            "record_ids": [30],
        },
        "audit": {
            "operation_id": None,
            "idempotency_key": None,
            "verification": {"result": "passed"},
        },
    }
    registry = load_registry()
    registry.validate_instance(request_schema, _request())
    registry.validate_instance(response_schema, response)
    response.update(
        success=False,
        status="failed_validation",
        data=None,
        error={
            "code": "failed_validation",
            "message": "The result failed validation.",
            "details": {},
            "retryable": False,
        },
    )
    registry.validate_instance(response_schema, response)
