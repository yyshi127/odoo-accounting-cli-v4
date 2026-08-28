from __future__ import annotations

import copy
import io
import json
from typing import Any

import pytest

import odoo_accounting_cli_v4.cli as cli
from odoo_accounting_cli_v4.bridge.bank_transactions import (
    OdooBankTransactionListPort,
)
from odoo_accounting_cli_v4.bridge.currency_rates import OdooCurrencyConvertPort
from odoo_accounting_cli_v4.bridge.journal_entries import OdooJournalEntryPort
from odoo_accounting_cli_v4.bridge.product_accounting_profile import (
    OdooProductAccountingProfilePort,
)
from odoo_accounting_cli_v4.capabilities.bank_transactions import (
    list_bank_transactions,
    validate_bank_transaction_list_request,
)
from odoo_accounting_cli_v4.capabilities.currency_rates import (
    convert_currency,
    validate_currency_convert_request,
)
from odoo_accounting_cli_v4.capabilities.journal_entries import (
    check_journal_entry,
    validate_journal_entry_check_request,
)
from odoo_accounting_cli_v4.capabilities.product_accounting_profile import (
    get_product_accounting_profile,
    validate_product_accounting_profile_request,
)
from odoo_accounting_cli_v4.registry import load_registry

REQUEST_ID = "7bc39413-0d69-4092-9319-795d33f3167c"
CAPABILITIES = {
    "currency.convert": (
        "currency_convert",
        convert_currency,
        validate_currency_convert_request,
        "res.currency",
        OdooCurrencyConvertPort,
    ),
    "validation.journal_entry.check": (
        "validation_journal_entry_check",
        check_journal_entry,
        validate_journal_entry_check_request,
        "account.move",
        OdooJournalEntryPort,
    ),
    "bank.transaction.list": (
        "bank_transaction_list",
        list_bank_transactions,
        validate_bank_transaction_list_request,
        "account.bank.statement.line",
        OdooBankTransactionListPort,
    ),
    "product.accounting_profile.get": (
        "product_accounting_profile_get",
        get_product_accounting_profile,
        validate_product_accounting_profile_request,
        "product.product",
        OdooProductAccountingProfilePort,
    ),
}


def _request(parameters: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "context": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "zh_CN",
            "timezone": "Asia/Shanghai",
        },
        "parameters": parameters,
    }


def _currency_conversion() -> dict[str, Any]:
    return {
        "company_id": 7,
        "date": "2025-01-31",
        "amount": "125.50",
        "converted_amount": "892.31",
        "from_currency": {"id": 2, "code": "USD"},
        "to_currency": {"id": 1, "code": "CNY"},
    }


def _entry_line(
    line_id: int, account_id: int, debit: str, credit: str, balance: str
) -> dict[str, Any]:
    currency = {"id": 6, "code": "CNY"}
    return {
        "id": line_id,
        "sequence": 10,
        "display_type": "product",
        "name": f"Line {line_id}",
        "account": {
            "id": account_id,
            "code": str(account_id),
            "name": "Account",
        },
        "partner": None,
        "debit": debit,
        "credit": credit,
        "balance": balance,
        "company_currency": currency,
        "amount_currency": balance,
        "currency": currency,
        "date_maturity": None,
        "reconciled": False,
        "matching_number": None,
    }


def _journal_entry() -> dict[str, Any]:
    return {
        "id": 30,
        "name": None,
        "date": "2025-02-01",
        "state": "draft",
        "ref": "validation-fixture",
        "journal": {"id": 4, "code": "MISC", "name": "Miscellaneous"},
        "company_id": 7,
        "currency": {"id": 6, "code": "CNY"},
        "partner": None,
        "lines": [
            _entry_line(301, 101, "123.45", "0.00", "123.45"),
            _entry_line(302, 102, "0.00", "123.45", "-123.45"),
        ],
        "totals": {"debit": "123.45", "credit": "123.45", "balance": "0.00"},
    }


def _bank_transaction() -> dict[str, Any]:
    return {
        "id": 20,
        "company_id": 7,
        "date": "2025-01-25",
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


def _product_profile() -> dict[str, Any]:
    unavailable_account = {
        "available": False,
        "reason_code": "module_uninstalled",
        "account": None,
    }
    unavailable_selection = {
        "available": False,
        "reason_code": "module_uninstalled",
        "value": None,
    }
    return {
        "company_id": 7,
        "product": {
            "id": 31,
            "name": "Office Chair / Blue",
            "default_code": "CHAIR-BLUE",
            "active": True,
            "company_id": None,
            "template_id": 21,
        },
        "template": {
            "id": 21,
            "name": "Office Chair",
            "company_id": None,
            "category_id": 11,
        },
        "category": {
            "id": 11,
            "name": "Office Furniture",
            "complete_name": "All / Office Furniture",
        },
        "modules": {"account": False, "stock_account": False},
        "accounts": {
            key: copy.deepcopy(unavailable_account)
            for key in (
                "income",
                "expense",
                "stock_valuation",
                "stock_input",
                "stock_output",
            )
        },
        "valuation": copy.deepcopy(unavailable_selection),
        "cost_method": copy.deepcopy(unavailable_selection),
    }


REQUESTS = {
    "currency.convert": _request(
        {
            "amount": "125.50",
            "from_currency_id": 2,
            "to_currency_id": 1,
            "date": "2025-01-31",
        }
    ),
    "validation.journal_entry.check": _request({"entry_id": 30}),
    "bank.transaction.list": _request({"limit": 1}),
    "product.accounting_profile.get": _request({"product_id": 31}),
}


class _SuccessPort:
    user_id = 42

    def __init__(self, capability_id: str) -> None:
        self.capability_id = capability_id
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def _page(self, **values: Any) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            **values,
        }

    def convert(self, **payload: Any) -> dict[str, Any]:
        self.calls.append(("convert", payload))
        return self._page(conversion=_currency_conversion())

    def check_entry(self, **payload: Any) -> dict[str, Any]:
        self.calls.append(("check_entry", payload))
        return self._page(entry=_journal_entry())

    def search_page(self, **payload: Any) -> dict[str, Any]:
        self.calls.append(("search_page", payload))
        return self._page(rows=[_bank_transaction()])

    def get_profile(self, **payload: Any) -> dict[str, Any]:
        self.calls.append(("get_profile", payload))
        return self._page(data=_product_profile())


EXPECTED_CALLS = {
    "currency.convert": (
        "convert",
        {
            "company_id": 7,
            "amount": "125.50",
            "from_currency_id": 2,
            "to_currency_id": 1,
            "conversion_date": "2025-01-31",
        },
    ),
    "validation.journal_entry.check": (
        "check_entry",
        {"company_id": 7, "entry_id": 30},
    ),
    "bank.transaction.list": (
        "search_page",
        {"company_id": 7, "after": None, "limit": 2},
    ),
    "product.accounting_profile.get": (
        "get_profile",
        {"company_id": 7, "product_id": 31},
    ),
}

EXPECTED_RECORD_IDS = {
    "currency.convert": [2, 1],
    "validation.journal_entry.check": [30],
    "bank.transaction.list": [20],
    "product.accounting_profile.get": [31],
}


@pytest.fixture(scope="module")
def registry() -> Any:
    return load_registry()


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_registry_cli_wiring_and_configured_port_dispatch(
    capability_id: str, monkeypatch: pytest.MonkeyPatch, registry: Any
) -> None:
    handler_key, handler, validator, model, port_type = CAPABILITIES[capability_id]
    descriptor = registry.describe(capability_id)

    assert descriptor["handler_key"] == handler_key
    assert cli._HANDLERS[handler_key] is handler
    assert cli._REQUEST_VALIDATORS[handler_key] is validator
    assert cli._CAPABILITY_MODELS[capability_id] == model

    target = object()
    client = object()

    class RuntimeConfig:
        def resolve(
            self, database: str, company_id: int, user_login: str
        ) -> object:
            assert (database, company_id, user_login) == (
                "odoo_cli_v4_dev",
                7,
                "v4-agent",
            )
            return target

    def bridge_factory(selected_target: object, **kwargs: str) -> object:
        assert selected_target is target
        assert kwargs == {"language": "zh_CN", "timezone": "Asia/Shanghai"}
        return client

    monkeypatch.setattr(cli, "load_runtime_config", lambda _path: RuntimeConfig())
    monkeypatch.setattr(cli, "OdooBridgeClient", bridge_factory)

    port = cli._configured_port_factory(capability_id, REQUESTS[capability_id])

    assert type(port) is port_type
    assert port._client is client


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_cli_emits_schema_valid_success_document(
    capability_id: str, monkeypatch: pytest.MonkeyPatch, registry: Any
) -> None:
    port = _SuccessPort(capability_id)
    monkeypatch.setattr(cli, "load_registry", lambda: registry)

    def port_factory(selected: str, request: dict[str, Any]) -> _SuccessPort:
        assert selected == capability_id
        assert request == REQUESTS[capability_id]
        return port

    stdout = io.StringIO()
    stderr = io.StringIO()
    result = cli.main(
        ["read", capability_id, "--request", "-"],
        stdin=io.StringIO(json.dumps(REQUESTS[capability_id])),
        stdout=stdout,
        stderr=stderr,
        port_factory=port_factory,
    )

    document = json.loads(stdout.getvalue())
    descriptor = registry.describe(capability_id)
    assert result == 0
    assert stderr.getvalue() == ""
    assert port.calls == [EXPECTED_CALLS[capability_id]]
    assert document["success"] is True
    assert document["capability"] == capability_id
    assert document["status"] == "verified"
    assert document["odoo"] == {
        "database": "odoo_cli_v4_dev",
        "company_id": 7,
        "user_id": 42,
        "model": CAPABILITIES[capability_id][3],
        "record_ids": EXPECTED_RECORD_IDS[capability_id],
    }
    registry.validate_instance(descriptor["schemas"]["response"], document)
