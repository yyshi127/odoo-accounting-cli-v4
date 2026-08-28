from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from odoo_accounting_cli_v4.capabilities.bank_transactions import (
    BankTransactionListError,
    list_bank_transactions,
    validate_bank_transaction_list_request,
)
from odoo_accounting_cli_v4.registry import InstanceValidationError, load_registry

REQUEST_ID = "123e4567-e89b-42d3-a456-426614174000"


def _request(*, company_id: int = 7, limit: int = 2, cursor: str | None = None) -> dict:
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
        "parameters": {"limit": limit, "cursor": cursor},
    }


def _row(record_id: int, transaction_date: str, **changes: object) -> dict:
    row = {
        "id": record_id,
        "company_id": 7,
        "date": transaction_date,
        "payment_date": "2025-01-26",
        "name": "Customer transfer",
        "reference": "BANK/42",
        "partner": {"id": 16, "name": "Acme"},
        "journal": {"id": 9, "code": "BNK1", "name": "Bank"},
        "amount": "125.50",
        "currency": {"id": 2, "code": "USD"},
        "move": {"id": 30, "name": "BNK1/2025/0001", "state": "posted"},
        "reconciled": False,
    }
    row.update(changes)
    return row


class FakePort:
    def __init__(
        self,
        *,
        rows: list[dict] | None = None,
        company_visible: bool = True,
        module_installed: bool = True,
        access_allowed: bool = True,
    ) -> None:
        self.rows = rows or []
        self.company_visible = company_visible
        self.module_installed = module_installed
        self.access_allowed = access_allowed
        self.user_id = 5
        self.calls: list[dict] = []

    def search_page(
        self,
        *,
        company_id: int,
        after: list[object] | None,
        limit: int,
    ) -> dict:
        self.calls.append(
            {"company_id": company_id, "after": after, "limit": limit}
        )
        return {
            "user_id": self.user_id,
            "company_visible": self.company_visible,
            "module_installed": self.module_installed,
            "access_allowed": self.access_allowed,
            "rows": self.rows[:limit],
        }


def test_list_uses_company_scope_defaults_and_date_id_keyset() -> None:
    rows = [
        _row(21, "2025-01-25"),
        _row(20, "2025-01-25"),
        _row(30, "2025-01-24"),
    ]
    first_port = FakePort(rows=rows)

    first = list_bank_transactions(first_port, _request(limit=2))

    assert first["items"] == rows[:2]
    assert first["has_more"] is True
    assert isinstance(first["next_cursor"], str)
    assert first_port.calls == [
        {"company_id": 7, "after": None, "limit": 3}
    ]

    second_port = FakePort(rows=[rows[2]])
    second = list_bank_transactions(
        second_port, _request(limit=2, cursor=first["next_cursor"])
    )
    assert second == {
        "items": [rows[2]],
        "has_more": False,
        "next_cursor": None,
    }
    assert second_port.calls == [
        {"company_id": 7, "after": ["2025-01-25", 20], "limit": 3}
    ]


def test_default_and_maximum_limits_are_closed() -> None:
    request = _request()
    request["parameters"] = {}
    port = FakePort()
    assert list_bank_transactions(port, request) == {
        "items": [],
        "has_more": False,
        "next_cursor": None,
    }
    assert port.calls == [{"company_id": 7, "after": None, "limit": 101}]

    request = _request(limit=1000)
    port = FakePort()
    list_bank_transactions(port, request)
    assert port.calls[0]["limit"] == 1001

    request["parameters"]["limit"] = 1001
    with pytest.raises(BankTransactionListError) as caught:
        list_bank_transactions(FakePort(), request)
    assert caught.value.code == "invalid_request"


def test_cursor_is_bound_to_database_company_and_user() -> None:
    first = list_bank_transactions(
        FakePort(rows=[_row(21, "2025-01-25"), _row(20, "2025-01-24")]),
        _request(limit=1),
    )
    cursor = first["next_cursor"]
    assert cursor

    mutations = [
        lambda request: request["context"].update(database="other"),
        lambda request: request["context"].update(company_id=8),
        lambda request: request["context"].update(user_login="other"),
    ]
    for mutation in mutations:
        request = _request(limit=1, cursor=cursor)
        mutation(request)
        port = FakePort()
        with pytest.raises(BankTransactionListError) as caught:
            list_bank_transactions(port, request)
        assert caught.value.code == "invalid_cursor"
        assert port.calls == []


@pytest.mark.parametrize(
    "rows",
    [
        [_row(20, "2025-01-25"), _row(21, "2025-01-25")],
        [_row(20, "2025-01-24"), _row(21, "2025-01-25")],
        [_row(20, "2025-01-25"), _row(20, "2025-01-24")],
    ],
)
def test_rows_must_be_unique_and_strictly_date_id_descending(
    rows: list[dict],
) -> None:
    with pytest.raises(BankTransactionListError) as caught:
        list_bank_transactions(FakePort(rows=rows), _request())
    assert caught.value.code == "failed_validation"


@pytest.mark.parametrize(
    "mutation",
    [
        lambda row: row.update(extra=True),
        lambda row: row.update(company_id=8),
        lambda row: row.update(date="2025/01/25"),
        lambda row: row.update(payment_date="2025-02-30"),
        lambda row: row.update(name=""),
        lambda row: row.update(reference=1),
        lambda row: row.update(partner={"id": True, "name": "Acme"}),
        lambda row: row.update(journal={"id": 9, "code": "", "name": "Bank"}),
        lambda row: row.update(amount="1e2"),
        lambda row: row.update(currency={"id": 2, "code": "USDX"}),
        lambda row: row.update(move={"id": 30, "name": "M", "state": "deleted"}),
        lambda row: row.update(reconciled=1),
    ],
)
def test_invalid_rows_never_become_verified(mutation) -> None:
    row = _row(20, "2025-01-25")
    mutation(row)

    with pytest.raises(BankTransactionListError) as caught:
        list_bank_transactions(FakePort(rows=[row]), _request())

    assert caught.value.code == "failed_validation"
    assert caught.value.exit_code == 8


def test_nullable_fields_are_preserved_without_fabricating_relations() -> None:
    row = _row(
        20,
        "2025-01-25",
        payment_date=None,
        name=None,
        reference=None,
        partner=None,
    )

    assert list_bank_transactions(FakePort(rows=[row]), _request())["items"] == [
        row
    ]


@pytest.mark.parametrize(
    ("port", "code"),
    [
        (
            FakePort(module_installed=False, access_allowed=False),
            "uninstalled",
        ),
        (FakePort(access_allowed=False), "unauthorized"),
        (FakePort(company_visible=False), "company_unavailable"),
    ],
)
def test_runtime_availability_failures_are_typed(
    port: FakePort, code: str
) -> None:
    with pytest.raises(BankTransactionListError) as caught:
        list_bank_transactions(port, _request())
    assert caught.value.code == code


def test_malformed_bridge_page_is_failed_validation() -> None:
    class Broken(FakePort):
        def search_page(self, **_kwargs) -> dict:
            raise ValueError("bad page")

    with pytest.raises(BankTransactionListError) as caught:
        list_bank_transactions(Broken(), _request())
    assert caught.value.code == "failed_validation"
    assert caught.value.exit_code == 8


@pytest.mark.parametrize(
    "mutation",
    [
        lambda request: request.update(extra=True),
        lambda request: request.update(schema_version="v2"),
        lambda request: request.update(request_id="not-a-uuid"),
        lambda request: request["context"].update(extra=True),
        lambda request: request["context"].update(company_id=True),
        lambda request: request["context"].update(database=" "),
        lambda request: request["parameters"].update(extra=True),
        lambda request: request["parameters"].update(limit=0),
        lambda request: request["parameters"].update(cursor=""),
    ],
)
def test_python_contract_rejects_invalid_requests(mutation) -> None:
    request = _request()
    mutation(request)
    with pytest.raises(BankTransactionListError) as caught:
        validate_bank_transaction_list_request(request)
    assert caught.value.code == "invalid_request"
    assert caught.value.exit_code == 2


def _success_response(data: dict) -> dict:
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "success": True,
        "capability": "bank.transaction.list",
        "status": "verified",
        "data": data,
        "warnings": [],
        "error": None,
        "odoo": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_id": 5,
            "model": "account.bank.statement.line",
            "record_ids": [20],
        },
        "audit": {
            "operation_id": None,
            "idempotency_key": None,
            "verification": {"result": "passed"},
        },
    }


def test_specialized_schemas_accept_success_and_error_documents() -> None:
    schema_dir = Path(__file__).parents[2] / "schemas" / "v1"
    capability = "bank.transaction.list"
    assert (schema_dir / f"{capability}.request.schema.json").is_file()
    assert (schema_dir / f"{capability}.response.schema.json").is_file()

    registry = load_registry()
    registry.validate_instance(
        f"schemas/v1/{capability}.request.schema.json", _request()
    )
    response = _success_response(
        {
            "items": [_row(20, "2025-01-25")],
            "has_more": False,
            "next_cursor": None,
        }
    )
    registry.validate_instance(
        f"schemas/v1/{capability}.response.schema.json", response
    )

    error_response = deepcopy(response)
    error_response.update(
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
    registry.validate_instance(
        f"schemas/v1/{capability}.response.schema.json", error_response
    )


def test_schema_and_python_reject_amount_with_trailing_newline() -> None:
    row = _row(20, "2025-01-25", amount="125.50\n")
    response = _success_response(
        {"items": [row], "has_more": False, "next_cursor": None}
    )
    with pytest.raises(InstanceValidationError):
        load_registry().validate_instance(
            "schemas/v1/bank.transaction.list.response.schema.json", response
        )
    with pytest.raises(BankTransactionListError):
        list_bank_transactions(FakePort(rows=[row]), _request())
