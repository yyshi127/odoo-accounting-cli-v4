from __future__ import annotations

import hashlib
import json
from copy import deepcopy

import pytest

from odoo_accounting_cli_v4.capabilities.core_writes import (
    CORE_WRITE_CAPABILITY_IDS,
    CoreWriteError,
    execute_core_write,
    validate_core_write_request,
)

CAPABILITIES = {
    "account.account.create",
    "account.account.update",
    "account.account.archive",
    "account.account.restore",
    "journal.create",
    "journal.update",
    "journal.archive",
    "journal.restore",
    "tax.create",
    "tax.update",
    "tax.archive",
    "tax.restore",
}
PARAMETERS = {
    "account.account.create": {
        "code": "1100",
        "name": "Trade Receivables",
        "account_type": "asset_receivable",
    },
    "account.account.update": {
        "account_id": 21,
        "changes": {"name": "Customer Receivables", "reconcile": True},
    },
    "account.account.archive": {"account_id": 22},
    "account.account.restore": {"account_id": 23},
    "journal.create": {"name": "Bank", "code": "bnk", "type": "bank"},
    "journal.update": {
        "journal_id": 31,
        "changes": {"code": "bn2", "currency_id": None},
    },
    "journal.archive": {"journal_id": 32},
    "journal.restore": {"journal_id": 33},
    "tax.create": {
        "name": "Sales Tax 15%",
        "type_tax_use": "sale",
        "amount_type": "percent",
        "amount": 15.0,
    },
    "tax.update": {
        "tax_id": 41,
        "changes": {"amount": 12.5, "invoice_label": None},
    },
    "tax.archive": {"tax_id": 42},
    "tax.restore": {"tax_id": 43},
}
MODELS = {
    "account.account": "account.account",
    "journal": "account.journal",
    "tax": "account.tax",
}


def _request(capability_id: str, parameters: dict | None = None) -> dict:
    return {
        "schema_version": "v1",
        "request_id": "31f91531-a230-4dde-a8bf-e56bb03bdaba",
        "context": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": deepcopy(
            PARAMETERS[capability_id] if parameters is None else parameters
        ),
    }


def _digest(value: object) -> str:
    canonical = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(canonical).hexdigest()[:32]


def _key(capability_id: str, request: dict | None = None) -> str:
    selected = _request(capability_id) if request is None else request
    parameters = validate_core_write_request(capability_id, selected)[2]
    if capability_id.endswith(".create"):
        return f"{capability_id}:7:{_digest(parameters)}"
    if capability_id.endswith(".update"):
        primary = {
            "account.account.update": "account_id",
            "journal.update": "journal_id",
            "tax.update": "tax_id",
        }[capability_id]
        return f"{capability_id}:{parameters[primary]}:{_digest(parameters['changes'])}"
    primary = (
        "account_id"
        if capability_id.startswith("account.account.")
        else "journal_id"
        if capability_id.startswith("journal.")
        else "tax_id"
    )
    return f"{capability_id}:{parameters[primary]}"


def _result(capability_id: str, **changes: object) -> dict:
    parameters = PARAMETERS[capability_id]
    prefix = capability_id.rsplit(".", 1)[0]
    model = MODELS[prefix]
    record_id = (
        901
        if capability_id == "account.account.create"
        else 902
        if capability_id == "journal.create"
        else 903
        if capability_id == "tax.create"
        else parameters.get(
            "account_id", parameters.get("journal_id", parameters.get("tax_id"))
        )
    )
    result = {
        "model": model,
        "id": record_id,
        "name": "Configured record",
        "state": "archived" if capability_id.endswith(".archive") else "active",
        "company_id": 7,
        "move_type": None,
        "source_id": None,
        "line_ids": [],
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }
    result.update(changes)
    return result


class FakePort:
    user_id = 42

    def __init__(self, capability_id: str, *, result: dict | None = None) -> None:
        self.capability_id = capability_id
        self.result = deepcopy(_result(capability_id) if result is None else result)
        self.calls: list[dict] = []

    def execute(self, **kwargs: object) -> dict:
        self.calls.append(deepcopy(kwargs))
        return {
            "user_id": 42,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "idempotent_replay": False,
            "result": deepcopy(self.result),
        }


@pytest.mark.parametrize("capability_id", sorted(CAPABILITIES))
def test_accounting_configuration_contract_and_port_payload(
    capability_id: str,
) -> None:
    assert capability_id in CORE_WRITE_CAPABILITY_IDS
    request = _request(capability_id)
    normalized = validate_core_write_request(capability_id, request)[2]
    port = FakePort(capability_id)

    data = execute_core_write(
        port, capability_id, request, _key(capability_id), capability_id
    )

    assert data == {
        "idempotent_replay": False,
        "result": _result(capability_id),
    }
    assert port.calls == [
        {
            "capability_id": capability_id,
            "company_id": 7,
            "idempotency_key": _key(capability_id),
            "confirmation": capability_id,
            "parameters": normalized,
        }
    ]


def test_create_defaults_and_normalization_are_closed() -> None:
    account = validate_core_write_request(
        "account.account.create",
        _request(
            "account.account.create",
            {
                "code": " ab.10 ",
                "name": " Trade Receivables ",
                "account_type": "asset_receivable",
            },
        ),
    )[2]
    assert account == {
        "code": "ab.10",
        "name": "Trade Receivables",
        "account_type": "asset_receivable",
        "reconcile": True,
        "currency_id": None,
    }

    journal = validate_core_write_request(
        "journal.create",
        _request(
            "journal.create",
            {"name": " Bank ", "code": " bnk ", "type": "bank"},
        ),
    )[2]
    assert journal == {
        "name": "Bank",
        "code": "BNK",
        "type": "bank",
        "sequence": None,
        "currency_id": None,
        "default_account_id": None,
    }

    tax = validate_core_write_request(
        "tax.create",
        _request(
            "tax.create",
            {
                "name": " Sales Tax ",
                "type_tax_use": "sale",
                "amount_type": "percent",
                "amount": 15.0,
            },
        ),
    )[2]
    assert tax == {
        "name": "Sales Tax",
        "type_tax_use": "sale",
        "amount_type": "percent",
        "amount": "15",
        "sequence": None,
        "tax_group_id": None,
        "invoice_label": None,
        "price_include_override": None,
        "include_base_amount": False,
        "is_base_affected": True,
    }


def test_updates_normalize_only_present_changes() -> None:
    journal = validate_core_write_request(
        "journal.update",
        _request(
            "journal.update",
            {"journal_id": 31, "changes": {"name": " Cash ", "code": " cs2 "}},
        ),
    )[2]
    assert journal == {
        "journal_id": 31,
        "changes": {"name": "Cash", "code": "CS2"},
    }
    tax = validate_core_write_request(
        "tax.update",
        _request(
            "tax.update",
            {
                "tax_id": 41,
                "changes": {"amount": -20.500, "invoice_label": " VAT "},
            },
        ),
    )[2]
    assert tax == {
        "tax_id": 41,
        "changes": {"amount": "-20.5", "invoice_label": "VAT"},
    }


def test_account_reconcile_defaults_and_type_change_are_odoo_compatible() -> None:
    expense = validate_core_write_request(
        "account.account.create",
        _request(
            "account.account.create",
            {"code": "6100", "name": "Expense", "account_type": "expense"},
        ),
    )[2]
    assert expense["reconcile"] is False

    update = validate_core_write_request(
        "account.account.update",
        _request(
            "account.account.update",
            {
                "account_id": 21,
                "changes": {"account_type": "liability_payable"},
            },
        ),
    )[2]
    assert update["changes"] == {
        "account_type": "liability_payable",
        "reconcile": True,
    }


def test_tax_amount_accepts_exactly_four_decimal_places() -> None:
    normalized = validate_core_write_request(
        "tax.update",
        _request("tax.update", {"tax_id": 41, "changes": {"amount": 0.1234}}),
    )[2]
    assert normalized["changes"]["amount"] == "0.1234"


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    [
        (
            "account.account.create",
            {"code": "11-00", "name": "Receivable", "account_type": "asset_cash"},
        ),
        (
            "account.account.create",
            {"code": "1100", "name": " ", "account_type": "asset_cash"},
        ),
        (
            "account.account.update",
            {"account_id": 21, "changes": {}},
        ),
        (
            "account.account.update",
            {"account_id": 21, "changes": {"reconcile": 1}},
        ),
        (
            "account.account.create",
            {
                "code": "1100",
                "name": "Receivable",
                "account_type": "asset_receivable",
                "reconcile": False,
            },
        ),
        (
            "account.account.update",
            {
                "account_id": 21,
                "changes": {
                    "account_type": "liability_payable",
                    "reconcile": False,
                },
            },
        ),
        (
            "journal.create",
            {"name": "Bank", "code": "BNK", "type": "other"},
        ),
        (
            "journal.update",
            {"journal_id": 31, "changes": {"type": "general"}},
        ),
        (
            "journal.update",
            {"journal_id": 31, "changes": {"sequence": -1}},
        ),
        (
            "tax.create",
            {
                "name": "Tax",
                "type_tax_use": "sale",
                "amount_type": "group",
                "amount": 10,
            },
        ),
        (
            "tax.create",
            {
                "name": "Tax",
                "type_tax_use": "sale",
                "amount_type": "fixed",
                "amount": True,
            },
        ),
        (
            "tax.create",
            {
                "name": "Tax",
                "type_tax_use": "sale",
                "amount_type": "fixed",
                "amount": float("nan"),
            },
        ),
        (
            "tax.create",
            {
                "name": "Tax",
                "type_tax_use": "sale",
                "amount_type": "fixed",
                "amount": 1000001,
            },
        ),
        (
            "tax.update",
            {"tax_id": 41, "changes": {"amount": 0.12345}},
        ),
        ("tax.update", {"tax_id": 41, "changes": {}}),
        ("tax.archive", {"tax_id": 0}),
    ],
)
def test_accounting_configuration_rejects_invalid_inputs(
    capability_id: str, parameters: dict
) -> None:
    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request(capability_id, _request(capability_id, parameters))
    assert caught.value.code == "invalid_request"


@pytest.mark.parametrize("capability_id", sorted(CAPABILITIES))
def test_keys_and_exact_confirmation_are_enforced(capability_id: str) -> None:
    request = _request(capability_id)
    with pytest.raises(CoreWriteError) as wrong_key:
        execute_core_write(
            FakePort(capability_id),
            capability_id,
            request,
            "wrong-key-0001",
            capability_id,
        )
    assert wrong_key.value.code == "invalid_idempotency_key"
    with pytest.raises(CoreWriteError) as wrong_confirmation:
        execute_core_write(
            FakePort(capability_id),
            capability_id,
            request,
            _key(capability_id),
            "accounting.invalid",
        )
    assert wrong_confirmation.value.code == "confirmation_required"


def test_create_keys_use_normalized_complete_parameters() -> None:
    first = _request(
        "journal.create",
        {"name": " Bank ", "code": " bnk ", "type": "bank"},
    )
    second = _request("journal.create", {"name": "Bank", "code": "BNK", "type": "bank"})
    assert _key("journal.create", first) == _key("journal.create", second)

    changed = _request(
        "journal.create",
        {"name": "Bank", "code": "BNK", "type": "bank", "sequence": 20},
    )
    assert _key("journal.create", first) != _key("journal.create", changed)


@pytest.mark.parametrize(
    ("capability_id", "change"),
    [
        ("account.account.create", {"model": "account.journal"}),
        ("account.account.update", {"id": 99}),
        ("account.account.archive", {"state": "active"}),
        ("journal.restore", {"state": "archived"}),
        ("tax.create", {"source_id": 41}),
        ("tax.update", {"line_ids": [1]}),
    ],
)
def test_accounting_configuration_results_fail_closed(
    capability_id: str, change: dict
) -> None:
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            FakePort(capability_id, result=_result(capability_id, **change)),
            capability_id,
            _request(capability_id),
            _key(capability_id),
            capability_id,
        )
    assert caught.value.code == "failed_validation"
