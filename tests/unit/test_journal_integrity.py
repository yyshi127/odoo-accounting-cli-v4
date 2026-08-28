from __future__ import annotations

import copy

import pytest

from odoo_accounting_cli_v4.capabilities.journal_integrity import (
    JournalIntegrityError,
    inspect_journal_integrity,
    validate_journal_integrity_request,
)
from odoo_accounting_cli_v4.registry import load_registry


REQUEST_ID = "a31769b9-c6ab-4975-9690-e96f1556bd34"


def _request() -> dict:
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "context": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": {},
    }


def _data() -> dict:
    return {
        "company_id": 7,
        "printing_date": "08/25/2026",
        "results": [
            {
                "journal_name": "Miscellaneous Operations",
                "restricted_by_hash_table": "X",
                "status": "no_data",
                "msg_cover": "There is no journal entry flagged yet.",
            },
            {
                "journal_name": "Sales (INV/2026/...)",
                "restricted_by_hash_table": "V",
                "status": "verified",
                "msg_cover": "Entries are correctly hashed",
                "first_move_name": "INV/2026/00001",
                "first_hash": "first-hash",
                "first_move_date": "01/02/2026",
                "last_move_name": "INV/2026/00009",
                "last_hash": "last-hash",
                "last_move_date": "08/25/2026",
            },
            {
                "journal_name": "Purchases (BILL/2026/...)",
                "restricted_by_hash_table": "V",
                "status": "corrupted",
                "msg_cover": "Corrupted data on journal entry with id 12.",
            },
        ],
    }


class FakePort:
    def __init__(
        self,
        *,
        data: dict | None = None,
        company_visible: bool = True,
        module_installed: bool = True,
        access_allowed: bool | None = None,
    ) -> None:
        self.user_id = 42
        self.data = copy.deepcopy(data)
        self.company_visible = company_visible
        self.module_installed = module_installed
        self.access_allowed = (
            company_visible and module_installed
            if access_allowed is None
            else access_allowed
        )
        self.calls: list[dict] = []

    def inspect(self, **kwargs) -> dict:
        self.calls.append(copy.deepcopy(kwargs))
        return {
            "user_id": self.user_id,
            "company_visible": self.company_visible,
            "module_installed": self.module_installed,
            "access_allowed": self.access_allowed,
            "data": copy.deepcopy(self.data),
        }


def test_inspection_preserves_the_native_odoo_19_result_fields() -> None:
    data = _data()
    port = FakePort(data=data)

    assert inspect_journal_integrity(port, _request()) == data
    assert port.calls == [{"company_id": 7}]


def test_empty_native_result_set_is_valid() -> None:
    data = {"company_id": 7, "printing_date": "08/25/2026", "results": []}

    assert inspect_journal_integrity(FakePort(data=data), _request()) == data


@pytest.mark.parametrize(
    "mutate",
    [
        lambda request: request.update(extra=True),
        lambda request: request["context"].update(company_id=True),
        lambda request: request["parameters"].update(extra=True),
    ],
)
def test_request_is_closed_and_accepts_no_parameters(mutate) -> None:
    request = _request()
    mutate(request)

    with pytest.raises(JournalIntegrityError) as caught:
        validate_journal_integrity_request(request)

    assert caught.value.code == "invalid_request"
    assert caught.value.exit_code == 2


@pytest.mark.parametrize(
    ("port", "code"),
    [
        (FakePort(company_visible=False), "company_unavailable"),
        (FakePort(module_installed=False), "module_uninstalled"),
        (FakePort(access_allowed=False), "unauthorized"),
    ],
)
def test_availability_failures_are_explicit(port: FakePort, code: str) -> None:
    with pytest.raises(JournalIntegrityError) as caught:
        inspect_journal_integrity(port, _request())

    assert caught.value.code == code


@pytest.mark.parametrize(
    "mutate",
    [
        lambda data: data.update(extra=True),
        lambda data: data.update(company_id=8),
        lambda data: data.update(printing_date=""),
        lambda data: data["results"][0].update(status="verified"),
        lambda data: data["results"][1].pop("last_hash"),
        lambda data: data["results"][2].update(first_hash="unexpected"),
        lambda data: data["results"][2].update(restricted_by_hash_table=True),
    ],
)
def test_native_result_shape_and_company_scope_fail_closed(mutate) -> None:
    data = _data()
    mutate(data)

    with pytest.raises(JournalIntegrityError) as caught:
        inspect_journal_integrity(FakePort(data=data), _request())

    assert caught.value.code == "failed_validation"


def test_wrong_bridge_user_fails_closed() -> None:
    class WrongUserPort(FakePort):
        def inspect(self, **kwargs) -> dict:
            page = super().inspect(**kwargs)
            page["user_id"] = self.user_id + 1
            return page

    with pytest.raises(JournalIntegrityError) as caught:
        inspect_journal_integrity(WrongUserPort(data=_data()), _request())

    assert caught.value.code == "failed_validation"


def test_specialized_schemas_accept_success_and_error_documents() -> None:
    request_schema = (
        "schemas/v1/diagnostic.journal_integrity.inspect.request.schema.json"
    )
    response_schema = (
        "schemas/v1/diagnostic.journal_integrity.inspect.response.schema.json"
    )
    response = {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "success": True,
        "capability": "diagnostic.journal_integrity.inspect",
        "status": "verified",
        "data": _data(),
        "warnings": [],
        "error": None,
        "odoo": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_id": 42,
            "model": "res.company",
            "record_ids": [7],
        },
        "audit": {
            "operation_id": None,
            "idempotency_key": None,
            "verification": None,
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
