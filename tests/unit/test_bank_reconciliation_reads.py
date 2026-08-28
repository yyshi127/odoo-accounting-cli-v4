from __future__ import annotations

import copy

import pytest

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4.bridge.bank_reconciliation import (
    OdooBankReconciliationPort,
)
from odoo_accounting_cli_v4.capabilities.bank_reconciliation import (
    BankReconciliationError,
    get_bank_transaction_reconciliation,
    list_bank_match_candidates,
    validate_bank_match_candidates_request,
    validate_bank_reconciliation_get_request,
)


def _request(capability_id: str, **changes: object) -> dict:
    parameters = {"transaction_id": 41}
    if capability_id == "bank.transaction.match_candidates.list":
        parameters.update({"limit": 1, "cursor": None})
    parameters.update(changes)
    return {
        "schema_version": "v1",
        "request_id": "b9f91531-a230-4dde-a8bf-e56bb03bdaba",
        "context": {
            "database": "v4-dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": parameters,
    }


def _line(record_id: int) -> dict:
    return {
        "id": record_id,
        "account_id": 31,
        "partner_id": 21,
        "currency_id": 6,
        "balance": "125.00",
        "amount_currency": "125.00",
        "amount_residual": "0.00",
        "amount_residual_currency": "0.00",
    }


def _reconciliation_result() -> dict:
    return {
        "transaction": {
            "id": 41,
            "company_id": 7,
            "move_id": 141,
            "move_state": "posted",
            "date": "2026-08-20",
            "journal_id": 8,
            "partner_id": 21,
            "amount": "125.00",
            "currency_id": 6,
            "foreign_currency_id": None,
            "amount_currency": "125.00",
            "amount_residual": "0.00",
            "is_reconciled": True,
            "checked": True,
        },
        "liquidity_line": _line(201),
        "suspense_line": None,
        "matched_lines": [
            {
                "bank_move_line_id": 202,
                "source_line_id": 301,
                "source_move_id": 401,
                "account_id": 31,
                "partner_id": 21,
                "currency_id": 6,
                "applied_balance": "-125.00",
                "applied_amount_currency": "-125.00",
                "source_amount_residual": "0.00",
                "source_amount_residual_currency": "0.00",
                "full_reconcile_id": 501,
            }
        ],
        "writeoff_lines": [
            {
                "id": 203,
                "name": "Bank fee",
                "account_id": 71,
                "partner_id": 21,
                "currency_id": 6,
                "balance": "-2.50",
                "amount_currency": "-2.50",
            }
        ],
        "payment_ids": [61],
    }


def _candidate(record_id: int, line_date: str) -> dict:
    return {
        "id": record_id,
        "date": line_date,
        "invoice_date": "2026-08-10",
        "date_maturity": "2026-09-10",
        "state": "posted",
        "move": {
            "id": 1000 + record_id,
            "name": f"MISC/2026/{record_id:04d}",
            "move_type": "entry",
            "ref": f"REF-{record_id}",
        },
        "label": f"Candidate {record_id}",
        "account": {
            "id": 31,
            "code": "220200",
            "name": "Suspense",
            "account_type": "asset_current",
        },
        "partner": {"id": 21, "name": "Customer"},
        "journal": {"id": 8, "code": "BNK1", "name": "Bank", "type": "bank"},
        "company_id": 7,
        "company_currency": {"id": 6, "code": "CNY"},
        "currency": {"id": 6, "code": "CNY"},
        "balance": "125.00",
        "amount_currency": "125.00",
        "amount_residual": "125.00",
        "amount_residual_currency": "125.00",
        "matching_number": None,
        "reconciliation_model": None,
    }


class FakePort:
    user_id = 42

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []
        self.rows = [_candidate(52, "2026-08-19"), _candidate(51, "2026-08-18")]

    def get(self, **kwargs) -> dict:
        self.calls.append(("get", copy.deepcopy(kwargs)))
        return {
            "user_id": 42,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "result": _reconciliation_result(),
        }

    def read_candidates_page(self, **kwargs) -> dict:
        self.calls.append(("candidates", copy.deepcopy(kwargs)))
        start = 0 if kwargs["after"] is None else 1
        return {
            "user_id": 42,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "rows": copy.deepcopy(self.rows[start : start + kwargs["limit"]]),
        }


def test_get_validates_the_exact_reconciliation_structure() -> None:
    request = _request("bank.transaction.reconciliation.get")
    assert validate_bank_reconciliation_get_request(request)[2] == 41
    port = FakePort()
    data = get_bank_transaction_reconciliation(port, request)
    assert data == _reconciliation_result()
    assert port.calls == [("get", {"company_id": 7, "transaction_id": 41})]

    malformed = FakePort()
    original_get = malformed.get

    def invalid_get(**kwargs) -> dict:
        page = original_get(**kwargs)
        page["result"]["transaction"]["company_id"] = 8
        return page

    malformed.get = invalid_get
    with pytest.raises(BankReconciliationError) as caught:
        get_bank_transaction_reconciliation(malformed, request)
    assert caught.value.code == "failed_validation"


def test_match_candidates_reuses_candidate_rows_and_binds_transaction_cursor() -> None:
    request = _request("bank.transaction.match_candidates.list")
    assert validate_bank_match_candidates_request(request)[2:4] == (41, 1)
    first = list_bank_match_candidates(FakePort(), request)
    assert [item["id"] for item in first["items"]] == [52]
    assert first["has_more"] is True
    assert first["next_cursor"]

    continued = list_bank_match_candidates(
        FakePort(),
        _request("bank.transaction.match_candidates.list", cursor=first["next_cursor"]),
    )
    assert [item["id"] for item in continued["items"]] == [51]

    with pytest.raises(BankReconciliationError) as caught:
        list_bank_match_candidates(
            FakePort(),
            _request(
                "bank.transaction.match_candidates.list",
                transaction_id=42,
                cursor=first["next_cursor"],
            ),
        )
    assert caught.value.code == "invalid_cursor"


def test_reconciliation_bridge_uses_only_the_two_fixed_actions() -> None:
    class Client:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict]] = []

        def invoke(self, action: str, payload: dict) -> dict:
            self.calls.append((action, copy.deepcopy(payload)))
            return (
                {
                    "user_id": 42,
                    "company_visible": True,
                    "module_installed": True,
                    "access_allowed": True,
                    "result": None,
                }
                if action.endswith("reconciliation.get")
                else {
                    "user_id": 42,
                    "company_visible": True,
                    "module_installed": True,
                    "access_allowed": True,
                    "rows": [],
                }
            )

    client = Client()
    port = OdooBankReconciliationPort(client)
    port.get(company_id=7, transaction_id=41)
    port.read_candidates_page(company_id=7, transaction_id=41, after=None, limit=101)
    assert client.calls == [
        (
            "account.bank.statement.line.reconciliation.get",
            {"company_id": 7, "transaction_id": 41},
        ),
        (
            "account.bank.statement.line.match_candidate.read_page",
            {"company_id": 7, "transaction_id": 41, "after": None, "limit": 101},
        ),
    ]


def test_cli_maps_both_reconciliation_reads_to_explicit_handlers() -> None:
    assert cli._HANDLERS["bank_transaction_reconciliation_get"] is (
        get_bank_transaction_reconciliation
    )
    assert cli._HANDLERS["bank_transaction_match_candidates_list"] is (
        list_bank_match_candidates
    )
    assert cli._REQUEST_VALIDATORS["bank_transaction_reconciliation_get"] is (
        validate_bank_reconciliation_get_request
    )
    assert cli._REQUEST_VALIDATORS["bank_transaction_match_candidates_list"] is (
        validate_bank_match_candidates_request
    )
    assert cli._CAPABILITY_MODELS["bank.transaction.reconciliation.get"] == (
        "account.bank.statement.line"
    )
    assert cli._CAPABILITY_MODELS["bank.transaction.match_candidates.list"] == (
        "account.move.line"
    )
