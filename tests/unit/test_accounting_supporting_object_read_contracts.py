from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from referencing import Registry, Resource

from odoo_accounting_cli_v4.capabilities.core_object_reads import (
    CoreObjectReadError,
    read_core_object,
    validate_core_object_read_request,
)
from odoo_accounting_cli_v4.contracts import success_document

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas" / "v1"
REQUEST_ID = "7bc39413-0d69-4092-9319-795d33f3167c"
CAPABILITY_IDS = (
    "asset.group.search",
    "asset.group.get",
    "report.budget_definition.search",
    "report.budget_definition.get",
    "report.budget_item.search",
    "report.budget_item.get",
    "tax.unit.search",
    "tax.unit.get",
    "account.return.account_status.search",
    "account.return.account_status.get",
)
SEARCH_IDS = frozenset(
    capability_id
    for capability_id in CAPABILITY_IDS
    if capability_id.endswith(".search")
)
PARAMETERS: dict[str, dict[str, Any]] = {
    "asset.group.search": {"query": "Vehicle", "limit": 10, "cursor": None},
    "asset.group.get": {"asset_group_id": 101},
    "report.budget_definition.search": {
        "query": "Operating",
        "limit": 10,
        "cursor": None,
    },
    "report.budget_definition.get": {"budget_definition_id": 201},
    "report.budget_item.search": {
        "budget_id": 201,
        "account_id": 31,
        "date_from": "2026-01-01",
        "date_to": "2026-12-31",
        "limit": 10,
        "cursor": None,
    },
    "report.budget_item.get": {"budget_item_id": 301},
    "tax.unit.search": {
        "query": "China",
        "country_id": 45,
        "main_company_only": True,
        "limit": 10,
        "cursor": None,
    },
    "tax.unit.get": {"tax_unit_id": 401},
    "account.return.account_status.search": {
        "return_id": 501,
        "account_id": 31,
        "statuses": ["reviewed", "todo"],
        "limit": 10,
        "cursor": None,
    },
    "account.return.account_status.get": {"account_status_id": 601},
}

ASSET_GROUP_ITEM = {
    "id": 101,
    "company_id": 7,
    "name": "Vehicles",
    "linked_asset_count": 3,
}
BUDGET_DEFINITION_ITEM = {
    "id": 201,
    "company_id": 7,
    "name": "Operating budget",
    "sequence": 10,
    "item_count": 2,
}
BUDGET_ITEM = {
    "id": 301,
    "company_id": 7,
    "budget_definition": {"id": 201, "name": "Operating budget"},
    "account": {"id": 31, "code": "6000", "name": "Expenses"},
    "amount": "1250.50",
    "date": "2026-06-30",
}
TAX_UNIT_ITEM = {
    "id": 401,
    "company_id": 7,
    "name": "China tax unit",
    "country": {"id": 45, "code": "CN", "name": "China"},
    "vat": None,
    "is_main_company": True,
    "fpos_synced": False,
}
ACCOUNT_STATUS_ITEM = {
    "id": 601,
    "company_id": 7,
    "return": {"id": 501, "name": "VAT Return 2026-Q2"},
    "account": {"id": 31, "code": "6000", "name": "Expenses"},
    "status": "reviewed",
}
ITEMS = {
    "asset.group.search": ASSET_GROUP_ITEM,
    "asset.group.get": ASSET_GROUP_ITEM,
    "report.budget_definition.search": BUDGET_DEFINITION_ITEM,
    "report.budget_definition.get": BUDGET_DEFINITION_ITEM,
    "report.budget_item.search": BUDGET_ITEM,
    "report.budget_item.get": BUDGET_ITEM,
    "tax.unit.search": TAX_UNIT_ITEM,
    "tax.unit.get": TAX_UNIT_ITEM,
    "account.return.account_status.search": ACCOUNT_STATUS_ITEM,
    "account.return.account_status.get": ACCOUNT_STATUS_ITEM,
}


def _request(capability_id: str) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": REQUEST_ID,
        "context": {
            "database": "v4-dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "zh_CN",
            "timezone": "Asia/Shanghai",
        },
        "parameters": deepcopy(PARAMETERS[capability_id]),
    }


def _load_schema(name: str) -> dict[str, Any]:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def _schema_validator(name: str) -> Draft202012Validator:
    resources: dict[str, Resource[Any]] = {}
    names = [
        "request.schema.json",
        "response.schema.json",
        *[
            f"{capability_id}.{kind}.schema.json"
            for capability_id in CAPABILITY_IDS
            for kind in ("request", "response")
        ],
    ]
    for resource_name in names:
        schema = _load_schema(resource_name)
        resource = Resource.from_contents(schema)
        resources[resource_name] = resource
        resources[schema["$id"]] = resource
    return Draft202012Validator(
        _load_schema(name),
        registry=Registry().with_resources(resources.items()),
        format_checker=FormatChecker(),
    )


class _Port:
    user_id = 42

    def __init__(self, item: dict[str, Any]) -> None:
        self.item = item

    def read(self, **_: Any) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "cursor_found": True,
            "items": [deepcopy(self.item)],
        }


class _EmptyPort:
    user_id = 42

    def read(self, **_: Any) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "cursor_found": True,
            "items": [],
        }


@pytest.mark.parametrize("capability_id", CAPABILITY_IDS)
def test_requests_are_closed_normalized_and_schema_valid(capability_id: str) -> None:
    request_name = f"{capability_id}.request.schema.json"
    response_name = f"{capability_id}.response.schema.json"
    Draft202012Validator.check_schema(_load_schema(request_name))
    Draft202012Validator.check_schema(_load_schema(response_name))
    _schema_validator(request_name).validate(_request(capability_id))

    _, _, normalized = validate_core_object_read_request(
        capability_id, _request(capability_id)
    )
    if capability_id in SEARCH_IDS:
        assert normalized["limit"] == 10
        assert normalized["cursor"] is None
    else:
        assert normalized == PARAMETERS[capability_id]

    invalid = _request(capability_id)
    invalid["parameters"]["sudo"] = True
    with pytest.raises(CoreObjectReadError) as caught:
        validate_core_object_read_request(capability_id, invalid)
    assert caught.value.code == "invalid_request"
    with pytest.raises(ValidationError):
        _schema_validator(request_name).validate(invalid)


@pytest.mark.parametrize("capability_id", CAPABILITY_IDS)
def test_runtime_and_response_schemas_share_the_minimal_closed_item(
    capability_id: str,
) -> None:
    item = deepcopy(ITEMS[capability_id])
    data = read_core_object(capability_id, _Port(item), _request(capability_id))
    expected = (
        {"items": [item], "has_more": False, "next_cursor": None}
        if capability_id in SEARCH_IDS
        else item
    )
    assert data == expected

    response = success_document(
        capability_id,
        data,
        request_id=REQUEST_ID,
        database="v4-dev",
        company_id=7,
        user_id=42,
        model="accounting.read",
        record_ids=[item["id"]],
    )
    _schema_validator(f"{capability_id}.response.schema.json").validate(response)

    invalid = deepcopy(response)
    invalid_item = (
        invalid["data"]["items"][0] if capability_id in SEARCH_IDS else invalid["data"]
    )
    invalid_item["extra"] = True
    with pytest.raises(ValidationError):
        _schema_validator(f"{capability_id}.response.schema.json").validate(invalid)


@pytest.mark.parametrize(
    "capability_id",
    [item for item in CAPABILITY_IDS if item.endswith(".get")],
)
def test_missing_get_uses_a_verified_empty_page_before_record_not_found(
    capability_id: str,
) -> None:
    port = _EmptyPort()

    with pytest.raises(CoreObjectReadError) as caught:
        read_core_object(capability_id, port, _request(capability_id))

    assert caught.value.code == "record_not_found"
    assert caught.value.exit_code == 4
    assert port.user_id == 42


def test_search_semantics_reject_invalid_filters_and_normalize_defaults() -> None:
    request = _request("tax.unit.search")
    request["parameters"].pop("main_company_only")
    _, _, normalized = validate_core_object_read_request("tax.unit.search", request)
    assert normalized["main_company_only"] is False

    request["parameters"]["main_company_only"] = None
    with pytest.raises(CoreObjectReadError):
        validate_core_object_read_request("tax.unit.search", request)

    reversed_dates = _request("report.budget_item.search")
    reversed_dates["parameters"].update(
        {"date_from": "2026-12-31", "date_to": "2026-01-01"}
    )
    with pytest.raises(CoreObjectReadError):
        validate_core_object_read_request("report.budget_item.search", reversed_dates)

    duplicate_statuses = _request("account.return.account_status.search")
    duplicate_statuses["parameters"]["statuses"] = ["todo", "todo"]
    with pytest.raises(CoreObjectReadError):
        validate_core_object_read_request(
            "account.return.account_status.search", duplicate_statuses
        )

    nullable_statuses = _request("account.return.account_status.search")
    nullable_statuses["parameters"]["statuses"] = None
    _schema_validator(
        "account.return.account_status.search.request.schema.json"
    ).validate(nullable_statuses)
    _, _, normalized = validate_core_object_read_request(
        "account.return.account_status.search", nullable_statuses
    )
    assert normalized["statuses"] is None


@pytest.mark.parametrize(
    ("capability_id", "field", "bad_value"),
    [
        ("asset.group.search", "linked_asset_count", -1),
        ("report.budget_definition.search", "company_id", 8),
        ("report.budget_item.search", "amount", "NaN"),
        ("tax.unit.search", "company_id", 8),
        ("tax.unit.search", "fpos_synced", 0),
        ("account.return.account_status.search", "status", "pending"),
    ],
)
def test_runtime_rejects_invalid_or_cross_company_items(
    capability_id: str, field: str, bad_value: object
) -> None:
    item = deepcopy(ITEMS[capability_id])
    item[field] = bad_value
    with pytest.raises(CoreObjectReadError) as caught:
        read_core_object(capability_id, _Port(item), _request(capability_id))
    assert caught.value.code == "failed_validation"


def test_account_return_status_preserves_an_untracked_native_state_as_null() -> None:
    item = deepcopy(ACCOUNT_STATUS_ITEM)
    item["status"] = None

    data = read_core_object(
        "account.return.account_status.get",
        _Port(item),
        _request("account.return.account_status.get"),
    )
    assert data["status"] is None

    response = success_document(
        "account.return.account_status.get",
        data,
        request_id=REQUEST_ID,
        database="v4-dev",
        company_id=7,
        user_id=42,
        model="account.audit.account.status",
        record_ids=[item["id"]],
    )
    _schema_validator(
        "account.return.account_status.get.response.schema.json"
    ).validate(response)


@pytest.mark.parametrize(
    ("capability_id", "field", "value"),
    [
        ("asset.group.get", "name", None),
        ("tax.unit.get", "vat", "CN" + "1" * 128),
    ],
)
def test_optional_native_text_fields_stay_aligned_with_response_schemas(
    capability_id: str, field: str, value: object
) -> None:
    item = deepcopy(ITEMS[capability_id])
    item[field] = value

    data = read_core_object(capability_id, _Port(item), _request(capability_id))
    response = success_document(
        capability_id,
        data,
        request_id=REQUEST_ID,
        database="v4-dev",
        company_id=7,
        user_id=42,
        model="accounting.read",
        record_ids=[item["id"]],
    )
    _schema_validator(f"{capability_id}.response.schema.json").validate(response)
