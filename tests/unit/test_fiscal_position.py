from __future__ import annotations

import copy

import pytest

from odoo_accounting_cli_v4.capabilities.fiscal_position import (
    FiscalPositionResolveError,
    resolve_fiscal_position,
    validate_fiscal_position_resolve_request,
)
from odoo_accounting_cli_v4.registry import load_registry


REQUEST_ID = "a31769b9-c6ab-4975-9690-e96f1556bd34"


def _request(parameters: dict | None = None) -> dict:
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
        "parameters": (
            {
                "partner_id": 31,
                "delivery_partner_id": 32,
                "account_id": 401,
                "tax_ids": [101, 102],
            }
            if parameters is None
            else parameters
        ),
    }


def _data() -> dict:
    return {
        "company_id": 7,
        "partner_id": 31,
        "delivery_partner_id": 32,
        "fiscal_position": {"id": 51, "name": "European Union"},
        "account_mapping": {"source_id": 401, "mapped_id": 402},
        "tax_mapping": {"source_ids": [101, 102], "mapped_ids": [201]},
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

    def resolve(self, **kwargs) -> dict:
        self.calls.append(copy.deepcopy(kwargs))
        return {
            "user_id": self.user_id,
            "company_visible": self.company_visible,
            "module_installed": self.module_installed,
            "access_allowed": self.access_allowed,
            "data": copy.deepcopy(self.data),
        }


def test_resolve_returns_only_the_native_resolution_and_requested_mappings() -> None:
    data = _data()
    port = FakePort(data=data)

    assert resolve_fiscal_position(port, _request()) == data
    assert port.calls == [
        {
            "company_id": 7,
            "partner_id": 31,
            "delivery_partner_id": 32,
            "account_id": 401,
            "tax_ids": [101, 102],
        }
    ]


def test_minimal_request_accepts_no_match_without_inventing_a_reason() -> None:
    request = _request({"partner_id": 31})
    data = {
        "company_id": 7,
        "partner_id": 31,
        "delivery_partner_id": None,
        "fiscal_position": None,
        "account_mapping": None,
        "tax_mapping": None,
    }

    assert resolve_fiscal_position(FakePort(data=data), request) == data


def test_no_match_requires_identity_mappings() -> None:
    data = _data()
    data.update(
        fiscal_position=None,
        account_mapping={"source_id": 401, "mapped_id": 999},
        tax_mapping={"source_ids": [101, 102], "mapped_ids": [999]},
    )

    with pytest.raises(FiscalPositionResolveError) as caught:
        resolve_fiscal_position(FakePort(data=data), _request())

    assert caught.value.code == "failed_validation"
    assert caught.value.exit_code == 8


@pytest.mark.parametrize(
    "parameters",
    [
        {},
        {"partner_id": True},
        {"partner_id": 31, "delivery_partner_id": 0},
        {"partner_id": 31, "account_id": "401"},
        {"partner_id": 31, "tax_ids": []},
        {"partner_id": 31, "tax_ids": [101, 101]},
        {"partner_id": 31, "unexpected": True},
    ],
)
def test_request_rejects_invalid_or_open_parameters(parameters: dict) -> None:
    with pytest.raises(FiscalPositionResolveError) as caught:
        validate_fiscal_position_resolve_request(_request(parameters))

    assert caught.value.code == "invalid_request"
    assert caught.value.exit_code == 2


@pytest.mark.parametrize(
    ("port", "code"),
    [
        (FakePort(company_visible=False), "company_unavailable"),
        (FakePort(module_installed=False), "module_uninstalled"),
        (FakePort(access_allowed=False), "unauthorized"),
        (FakePort(data=None), "record_not_found"),
    ],
)
def test_availability_and_missing_records_are_explicit(
    port: FakePort, code: str
) -> None:
    with pytest.raises(FiscalPositionResolveError) as caught:
        resolve_fiscal_position(port, _request())

    assert caught.value.code == code


@pytest.mark.parametrize(
    "mutate",
    [
        lambda data: data.update(extra=True),
        lambda data: data.update(company_id=8),
        lambda data: data.update(partner_id=30),
        lambda data: data.update(delivery_partner_id=33),
        lambda data: data["fiscal_position"].update(id=True),
        lambda data: data["account_mapping"].update(source_id=400),
        lambda data: data["tax_mapping"].update(source_ids=[102, 101]),
        lambda data: data["tax_mapping"].update(mapped_ids=[201, 201]),
    ],
)
def test_inconsistent_or_out_of_scope_results_fail_closed(mutate) -> None:
    data = _data()
    mutate(data)

    with pytest.raises(FiscalPositionResolveError) as caught:
        resolve_fiscal_position(FakePort(data=data), _request())

    assert caught.value.code == "failed_validation"


def test_wrong_bridge_user_fails_closed() -> None:
    class WrongUserPort(FakePort):
        def resolve(self, **kwargs) -> dict:
            page = super().resolve(**kwargs)
            page["user_id"] = self.user_id + 1
            return page

    with pytest.raises(FiscalPositionResolveError) as caught:
        resolve_fiscal_position(WrongUserPort(data=_data()), _request())

    assert caught.value.code == "failed_validation"


def test_specialized_schemas_accept_success_and_error_documents() -> None:
    request_schema = "schemas/v1/fiscal_position.resolve.request.schema.json"
    response_schema = "schemas/v1/fiscal_position.resolve.response.schema.json"
    response = {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "success": True,
        "capability": "fiscal_position.resolve",
        "status": "verified",
        "data": _data(),
        "warnings": [],
        "error": None,
        "odoo": {
            "database": "odoo_cli_v4_dev",
            "company_id": 7,
            "user_id": 42,
            "model": "account.fiscal.position",
            "record_ids": [51],
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
