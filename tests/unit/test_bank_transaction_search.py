from __future__ import annotations

import copy

import pytest

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4.bridge.bank_transactions import (
    OdooBankTransactionSearchPort,
)
from odoo_accounting_cli_v4.capabilities.bank_transactions import (
    BankTransactionListError,
    search_bank_transactions,
    validate_bank_transaction_search_request,
)


def _request(**changes: object) -> dict:
    parameters = {
        "date_from": "2026-08-01",
        "date_to": "2026-08-31",
        "journal_id": 8,
        "partner_id": 21,
        "reconciled": False,
        "query": "Transfer",
        "limit": 1,
        "cursor": None,
    }
    parameters.update(changes)
    return {
        "schema_version": "v1",
        "request_id": "a9f91531-a230-4dde-a8bf-e56bb03bdaba",
        "context": {
            "database": "v4-dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": parameters,
    }


def _row(record_id: int, day: int) -> dict:
    return {
        "id": record_id,
        "company_id": 7,
        "date": f"2026-08-{day:02d}",
        "payment_date": None,
        "name": f"Transfer {record_id}",
        "reference": None,
        "partner": {"id": 21, "name": "Customer"},
        "journal": {"id": 8, "code": "BNK1", "name": "Bank"},
        "amount": "100.00",
        "currency": {"id": 6, "code": "CNY"},
        "move": {"id": record_id + 100, "name": f"BNK/{record_id}", "state": "posted"},
        "reconciled": False,
    }


class FakePort:
    user_id = 42

    def __init__(self) -> None:
        self.rows = [_row(12, 20), _row(11, 19)]
        self.calls: list[dict] = []

    def search_page(self, **kwargs) -> dict:
        self.calls.append(copy.deepcopy(kwargs))
        after = kwargs["after"]
        start = 0 if after is None else 1
        return {
            "user_id": 42,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "rows": copy.deepcopy(self.rows[start : start + kwargs["limit"]]),
        }


def test_search_normalizes_filters_and_binds_the_cursor() -> None:
    _, _, filters, limit, cursor = validate_bank_transaction_search_request(_request())
    assert filters == {
        "date_from": "2026-08-01",
        "date_to": "2026-08-31",
        "journal_id": 8,
        "partner_id": 21,
        "reconciled": False,
        "query": "Transfer",
    }
    assert (limit, cursor) == (1, None)

    first_port = FakePort()
    first = search_bank_transactions(first_port, _request())
    assert [item["id"] for item in first["items"]] == [12]
    assert first["has_more"] is True
    assert first["next_cursor"]
    assert first_port.calls[0]["filters"] == filters

    continued = search_bank_transactions(
        FakePort(), _request(cursor=first["next_cursor"])
    )
    assert [item["id"] for item in continued["items"]] == [11]

    with pytest.raises(BankTransactionListError) as caught:
        search_bank_transactions(
            FakePort(), _request(partner_id=22, cursor=first["next_cursor"])
        )
    assert caught.value.code == "invalid_cursor"


def test_search_rejects_invalid_dates_and_filters() -> None:
    with pytest.raises(BankTransactionListError):
        validate_bank_transaction_search_request(_request(date_from="2026-09-01"))
    with pytest.raises(BankTransactionListError):
        validate_bank_transaction_search_request(_request(reconciled="false"))


def test_search_bridge_uses_the_fixed_filtered_action() -> None:
    class Client:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict]] = []

        def invoke(self, action: str, payload: dict) -> dict:
            self.calls.append((action, copy.deepcopy(payload)))
            return {
                "user_id": 42,
                "company_visible": True,
                "module_installed": True,
                "access_allowed": True,
                "rows": [],
            }

    client = Client()
    port = OdooBankTransactionSearchPort(client)
    filters = validate_bank_transaction_search_request(_request())[2]
    port.search_page(company_id=7, after=None, limit=2, filters=filters)
    assert port.user_id == 42
    assert client.calls == [
        (
            "account.bank.statement.line.search_page",
            {"company_id": 7, "after": None, "limit": 2, "filters": filters},
        )
    ]


def test_cli_maps_search_to_its_explicit_handler_validator_model_and_port(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert cli._HANDLERS["bank_transaction_search"] is search_bank_transactions
    assert (
        cli._REQUEST_VALIDATORS["bank_transaction_search"]
        is validate_bank_transaction_search_request
    )
    assert cli._CAPABILITY_MODELS["bank.transaction.search"] == (
        "account.bank.statement.line"
    )
    target = object()
    client = object()

    class RuntimeConfig:
        def resolve(self, *_args) -> object:
            return target

    monkeypatch.setattr(cli, "load_runtime_config", lambda _path: RuntimeConfig())
    monkeypatch.setattr(cli, "OdooBridgeClient", lambda *_args, **_kwargs: client)
    port = cli._configured_port_factory("bank.transaction.search", _request())
    assert type(port) is OdooBankTransactionSearchPort
    assert port._client is client
