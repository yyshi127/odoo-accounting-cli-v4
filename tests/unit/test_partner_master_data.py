from __future__ import annotations

import hashlib
import json
from copy import deepcopy

import pytest

from odoo_accounting_cli_v4.capabilities.core_object_reads import (
    CORE_OBJECT_READ_CAPABILITY_IDS,
    CoreObjectReadError,
    read_core_object,
    validate_core_object_read_request,
)
from odoo_accounting_cli_v4.capabilities.core_writes import (
    CORE_WRITE_CAPABILITY_IDS,
    CoreWriteError,
    execute_core_write,
    validate_core_write_request,
)

READ_CAPABILITIES = {"partner.search", "partner.get"}
WRITE_CAPABILITIES = {
    "partner.create",
    "partner.update",
    "partner.archive",
    "partner.restore",
    "partner.accounting.update",
    "partner.bank_account.create",
    "partner.bank_account.update",
    "partner.bank_account.archive",
    "partner.bank_account.restore",
}
WRITE_PARAMETERS = {
    "partner.create": {"name": "Acme", "company_type": "company"},
    "partner.update": {
        "partner_id": 21,
        "changes": {"reference": None, "email": "billing@example.com"},
    },
    "partner.archive": {"partner_id": 22},
    "partner.restore": {"partner_id": 23},
    "partner.accounting.update": {
        "partner_id": 24,
        "changes": {
            "property_account_receivable_id": 301,
            "property_payment_term_id": None,
        },
    },
    "partner.bank_account.create": {
        "partner_id": 21,
        "account_number": "JP1234567890",
    },
    "partner.bank_account.update": {
        "partner_bank_id": 31,
        "changes": {"account_holder_name": "Acme Treasury", "bank_id": None},
    },
    "partner.bank_account.archive": {"partner_bank_id": 32},
    "partner.bank_account.restore": {"partner_bank_id": 33},
}


def _request(parameters: dict) -> dict:
    return {
        "schema_version": "v1",
        "request_id": "a1f91531-a230-4dde-a8bf-e56bb03bdaba",
        "context": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": deepcopy(parameters),
    }


def _partner_item(**changes: object) -> dict:
    item = {
        "id": 21,
        "name": "Acme",
        "display_name": "Acme",
        "company_type": "company",
        "active": True,
        "vat": "JP123",
        "reference": None,
        "email": "billing@example.com",
        "phone": None,
        "mobile": None,
        "street": "1 Main Street",
        "street2": None,
        "city": "Tokyo",
        "zip": "100-0001",
        "state": {"id": 4, "name": "Tokyo"},
        "country": {"id": 110, "name": "Japan"},
        "language": "en_US",
        "company_id": None,
        "parent": None,
        "customer_rank": 1,
        "supplier_rank": 0,
    }
    item.update(changes)
    return item


class ReadPort:
    user_id = 42

    def __init__(self, items: list[dict]) -> None:
        self.items = deepcopy(items)
        self.calls: list[dict] = []

    def read(self, **kwargs: object) -> dict:
        self.calls.append(deepcopy(kwargs))
        return {
            "user_id": 42,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "cursor_found": True,
            "items": deepcopy(self.items),
        }


def test_partner_get_contract_and_dispatch() -> None:
    assert "partner.get" in CORE_OBJECT_READ_CAPABILITY_IDS
    request = _request({"partner_id": 21})
    assert validate_core_object_read_request("partner.get", request)[2] == {
        "partner_id": 21
    }
    port = ReadPort([_partner_item(company_id=7)])
    assert read_core_object("partner.get", port, request) == _partner_item(company_id=7)
    assert port.calls == [
        {
            "capability_id": "partner.get",
            "company_id": 7,
            "parameters": {"partner_id": 21},
        }
    ]


def test_partner_search_defaults_and_dispatch() -> None:
    assert "partner.search" in CORE_OBJECT_READ_CAPABILITY_IDS
    request = _request({})
    normalized = {
        "query": None,
        "active": None,
        "company_type": None,
        "customer": None,
        "supplier": None,
        "limit": 100,
        "cursor": None,
    }
    assert validate_core_object_read_request("partner.search", request)[2] == normalized
    port = ReadPort([_partner_item()])
    assert read_core_object("partner.search", port, request) == {
        "items": [_partner_item()],
        "has_more": False,
        "next_cursor": None,
    }
    assert port.calls[0]["parameters"] == {
        "query": None,
        "active": None,
        "company_type": None,
        "customer": None,
        "supplier": None,
        "after_id": None,
        "limit": 101,
    }


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    [
        ("partner.get", {"partner_id": 21, "extra": True}),
        ("partner.get", {"partner_id": True}),
        ("partner.search", {"extra": True}),
        ("partner.search", {"query": " Acme"}),
        ("partner.search", {"query": "x" * 201}),
        ("partner.search", {"active": 1}),
        ("partner.search", {"company_type": "organization"}),
        ("partner.search", {"company_type": []}),
        ("partner.search", {"customer": "yes"}),
        ("partner.search", {"supplier": 0}),
    ],
)
def test_partner_reads_reject_invalid_parameters(
    capability_id: str, parameters: dict
) -> None:
    with pytest.raises(CoreObjectReadError) as caught:
        validate_core_object_read_request(capability_id, _request(parameters))
    assert caught.value.code == "invalid_request"


@pytest.mark.parametrize(
    "change",
    [
        {"company_id": 8},
        {"company_type": "organization"},
        {"state": {"id": 4, "label": "Tokyo"}},
        {"customer_rank": -1},
        {"unexpected": True},
    ],
)
def test_partner_read_results_fail_closed(change: dict) -> None:
    item = _partner_item()
    item.update(change)
    with pytest.raises(CoreObjectReadError) as caught:
        read_core_object("partner.search", ReadPort([item]), _request({}))
    assert caught.value.code == "failed_validation"


def _write_request(capability_id: str) -> dict:
    return _request(WRITE_PARAMETERS[capability_id])


def _digest(value: object) -> str:
    canonical = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(canonical).hexdigest()[:32]


def _key(capability_id: str) -> str:
    parameters = WRITE_PARAMETERS[capability_id]
    if capability_id == "partner.create":
        normalized = {
            **parameters,
            "vat": None,
            "reference": None,
            "email": None,
            "phone": None,
            "mobile": None,
            "street": None,
            "street2": None,
            "city": None,
            "zip": None,
            "state_id": None,
            "country_id": None,
            "language": None,
        }
        return f"partner.create:{_digest(normalized)}"
    if capability_id in {"partner.update", "partner.accounting.update"}:
        return f"{capability_id}:{parameters['partner_id']}:{_digest(parameters['changes'])}"
    if capability_id in {"partner.archive", "partner.restore"}:
        return f"{capability_id}:{parameters['partner_id']}"
    if capability_id == "partner.bank_account.create":
        digest = hashlib.sha256(parameters["account_number"].encode()).hexdigest()[:32]
        return f"{capability_id}:{parameters['partner_id']}:{digest}"
    if capability_id == "partner.bank_account.update":
        return (
            f"{capability_id}:{parameters['partner_bank_id']}:"
            f"{_digest(parameters['changes'])}"
        )
    return f"{capability_id}:{parameters['partner_bank_id']}"


def _write_result(capability_id: str, **changes: object) -> dict:
    bank = capability_id.startswith("partner.bank_account.")
    parameters = WRITE_PARAMETERS[capability_id]
    record_id = (
        901
        if capability_id == "partner.create"
        else 902
        if capability_id == "partner.bank_account.create"
        else parameters.get("partner_id", parameters.get("partner_bank_id"))
    )
    state = "archived" if capability_id.endswith(".archive") else "active"
    result = {
        "model": "res.partner.bank" if bank else "res.partner",
        "id": record_id,
        "name": "JP1234567890" if bank else "Acme",
        "state": state,
        "company_id": 7,
        "move_type": None,
        "source_id": 21 if bank else None,
        "line_ids": [],
        "partial_reconcile_ids": [],
        "full_reconcile_id": None,
        "reconciled": False,
    }
    result.update(changes)
    return result


class WritePort:
    user_id = 42

    def __init__(self, capability_id: str, *, result: dict | None = None) -> None:
        self.capability_id = capability_id
        self.result = deepcopy(
            _write_result(capability_id) if result is None else result
        )
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


@pytest.mark.parametrize("capability_id", sorted(WRITE_CAPABILITIES))
def test_partner_write_contract_and_dispatch(capability_id: str) -> None:
    assert capability_id in CORE_WRITE_CAPABILITY_IDS
    request = _write_request(capability_id)
    normalized = validate_core_write_request(capability_id, request)[2]
    port = WritePort(capability_id)
    data = execute_core_write(
        port, capability_id, request, _key(capability_id), capability_id
    )
    assert data == {
        "idempotent_replay": False,
        "result": _write_result(capability_id),
    }
    assert port.calls[0] == {
        "capability_id": capability_id,
        "company_id": 7,
        "idempotency_key": _key(capability_id),
        "confirmation": capability_id,
        "parameters": normalized,
    }


def test_partner_create_contracts_fill_every_optional_field_with_null() -> None:
    partner = validate_core_write_request(
        "partner.create", _write_request("partner.create")
    )[2]
    assert set(partner) == {
        "name",
        "company_type",
        "vat",
        "reference",
        "email",
        "phone",
        "mobile",
        "street",
        "street2",
        "city",
        "zip",
        "state_id",
        "country_id",
        "language",
    }
    bank = validate_core_write_request(
        "partner.bank_account.create", _write_request("partner.bank_account.create")
    )[2]
    assert bank == {
        "partner_id": 21,
        "account_number": "JP1234567890",
        "account_holder_name": None,
        "bank_id": None,
        "currency_id": None,
    }


@pytest.mark.parametrize("capability_id", sorted(WRITE_CAPABILITIES))
def test_partner_writes_reject_an_arbitrary_parameter(capability_id: str) -> None:
    request = _write_request(capability_id)
    request["parameters"]["unexpected"] = True
    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request(capability_id, request)
    assert caught.value.code == "invalid_request"


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    [
        (
            "partner.create",
            {"name": "Acme [ODACV4:fake]", "company_type": "company"},
        ),
        (
            "partner.create",
            {
                "name": "Acme",
                "company_type": "company",
                "reference": "[ODACV4:fake]",
            },
        ),
        (
            "partner.update",
            {"partner_id": 21, "changes": {"reference": "[ODACV4:fake]"}},
        ),
        (
            "partner.update",
            {"partner_id": 21, "changes": {"name": "Acme [ODACV4:fake]"}},
        ),
        (
            "partner.bank_account.create",
            {"partner_id": 21, "account_number": "[ODACV4:fake]"},
        ),
        (
            "partner.bank_account.create",
            {
                "partner_id": 21,
                "account_number": "JP123",
                "account_holder_name": "Acme [ODACV4:fake]",
            },
        ),
        (
            "partner.bank_account.update",
            {
                "partner_bank_id": 31,
                "changes": {"account_number": "[ODACV4:fake]"},
            },
        ),
        (
            "partner.bank_account.update",
            {
                "partner_bank_id": 31,
                "changes": {"account_holder_name": "Acme [ODACV4:fake]"},
            },
        ),
    ],
)
def test_partner_writes_reject_reserved_marker(
    capability_id: str, parameters: dict
) -> None:
    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request(capability_id, _request(parameters))
    assert caught.value.code == "invalid_request"


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    [
        (
            "partner.update",
            {"partner_id": 21, "changes": {"unexpected": True}},
        ),
        (
            "partner.accounting.update",
            {"partner_id": 21, "changes": {"unexpected": True}},
        ),
        (
            "partner.bank_account.update",
            {"partner_bank_id": 31, "changes": {"unexpected": True}},
        ),
        (
            "partner.create",
            {"name": "Acme", "company_type": "company", "email": None},
        ),
        (
            "partner.update",
            {"partner_id": 21, "changes": {"email": " "}},
        ),
        (
            "partner.update",
            {"partner_id": 21, "changes": {"company_type": None}},
        ),
        (
            "partner.bank_account.create",
            {"partner_id": 21, "account_number": " JP123"},
        ),
        (
            "partner.bank_account.create",
            {
                "partner_id": 21,
                "account_number": "JP123",
                "account_holder_name": "",
            },
        ),
    ],
)
def test_partner_writes_reject_nested_or_string_contract_drift(
    capability_id: str, parameters: dict
) -> None:
    with pytest.raises(CoreWriteError) as caught:
        validate_core_write_request(capability_id, _request(parameters))
    assert caught.value.code == "invalid_request"


def test_partner_updates_preserve_explicit_null_clears() -> None:
    partner = validate_core_write_request(
        "partner.update",
        _request(
            {
                "partner_id": 21,
                "changes": {
                    "vat": None,
                    "reference": None,
                    "state_id": None,
                    "language": None,
                },
            }
        ),
    )[2]
    assert partner["changes"] == {
        "vat": None,
        "reference": None,
        "state_id": None,
        "language": None,
    }


@pytest.mark.parametrize("capability_id", sorted(WRITE_CAPABILITIES))
def test_partner_writes_reject_wrong_key_and_confirmation(capability_id: str) -> None:
    request = _write_request(capability_id)
    with pytest.raises(CoreWriteError) as wrong_key:
        execute_core_write(
            WritePort(capability_id),
            capability_id,
            request,
            "wrong-key-0001",
            capability_id,
        )
    assert wrong_key.value.code == "invalid_idempotency_key"
    with pytest.raises(CoreWriteError) as wrong_confirmation:
        execute_core_write(
            WritePort(capability_id),
            capability_id,
            request,
            _key(capability_id),
            "partner.invalid",
        )
    assert wrong_confirmation.value.code == "confirmation_required"


@pytest.mark.parametrize(
    ("capability_id", "change"),
    [
        ("partner.create", {"model": "res.users"}),
        ("partner.update", {"id": 99}),
        ("partner.archive", {"state": "active"}),
        ("partner.restore", {"state": "archived"}),
        ("partner.accounting.update", {"source_id": 24}),
        ("partner.bank_account.create", {"source_id": 99}),
        ("partner.bank_account.update", {"id": 99}),
        ("partner.bank_account.archive", {"state": "active"}),
        ("partner.bank_account.restore", {"state": "archived"}),
    ],
)
def test_partner_write_results_fail_closed(capability_id: str, change: dict) -> None:
    result = _write_result(capability_id, **change)
    with pytest.raises(CoreWriteError) as caught:
        execute_core_write(
            WritePort(capability_id, result=result),
            capability_id,
            _write_request(capability_id),
            _key(capability_id),
            capability_id,
        )
    assert caught.value.code == "failed_validation"
