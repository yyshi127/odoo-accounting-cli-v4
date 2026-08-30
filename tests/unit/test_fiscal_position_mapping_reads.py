from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from referencing import Registry, Resource

from odoo_accounting_cli_v4.bridge import core_object_reads_runtime as runtime
from odoo_accounting_cli_v4.capabilities.core_object_reads import (
    CORE_OBJECT_READ_CAPABILITY_IDS,
    CoreObjectReadError,
    list_fiscal_position_account_mappings,
    list_fiscal_position_tax_mappings,
    read_core_object,
    validate_core_object_read_request,
)
from odoo_accounting_cli_v4.contracts import success_document

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas" / "v1"
REQUEST_ID = "7bc39413-0d69-4092-9319-795d33f3167c"
CAPABILITIES = (
    "fiscal_position.account_mapping.list",
    "fiscal_position.tax_mapping.list",
)


def _request(
    *,
    fiscal_position_id: int = 9,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict[str, Any]:
    parameters: dict[str, Any] = {"fiscal_position_id": fiscal_position_id}
    if limit is not None:
        parameters["limit"] = limit
    if cursor is not None:
        parameters["cursor"] = cursor
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


def _account_item(record_id: int) -> dict[str, Any]:
    return {
        "id": record_id,
        "company_id": 7,
        "source_account": {"id": record_id + 100, "code": "4000", "name": "Sales"},
        "destination_account": {
            "id": record_id + 200,
            "code": "4100",
            "name": "Mapped sales",
        },
    }


def _tax_item(source_id: int, *destination_ids: int) -> dict[str, Any]:
    return {
        "source_tax": {"id": source_id, "name": f"Source {source_id}"},
        "destination_taxes": [
            {"id": destination_id, "name": f"Destination {destination_id}"}
            for destination_id in destination_ids
        ],
    }


class PagePort:
    user_id = 42

    def __init__(
        self,
        capability_id: str,
        items: list[dict[str, Any]],
        *,
        removes_all_taxes: bool = False,
    ) -> None:
        self.capability_id = capability_id
        self.items = items
        self.removes_all_taxes = removes_all_taxes
        self.calls: list[dict[str, Any]] = []

    def read(
        self,
        *,
        capability_id: str,
        company_id: int,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        assert capability_id == self.capability_id
        assert company_id == 7
        self.calls.append(deepcopy(parameters))
        after_id = parameters["after_id"]
        visible = [
            item
            for item in self.items
            if after_id is None
            or (
                item["source_tax"]["id"]
                if capability_id == "fiscal_position.tax_mapping.list"
                else item["id"]
            )
            > after_id
        ][: parameters["limit"]]
        page = {
            "user_id": self.user_id,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "cursor_found": True,
            "items": visible,
        }
        if capability_id == "fiscal_position.tax_mapping.list":
            page["removes_all_taxes"] = self.removes_all_taxes
        return page


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_request_is_closed_and_normalizes_required_scope(capability_id: str) -> None:
    assert capability_id in CORE_OBJECT_READ_CAPABILITY_IDS
    _, _, parameters = validate_core_object_read_request(
        capability_id, _request()
    )
    assert parameters == {"fiscal_position_id": 9, "limit": 100, "cursor": None}

    for invalid in ({}, {"fiscal_position_id": 0}, {"fiscal_position_id": 9, "x": 1}):
        request = _request()
        request["parameters"] = invalid
        with pytest.raises(CoreObjectReadError) as caught:
            validate_core_object_read_request(capability_id, request)
        assert caught.value.code == "invalid_request"


def test_account_mapping_uses_mapping_row_cursor_bound_to_fiscal_position() -> None:
    port = PagePort(
        "fiscal_position.account_mapping.list",
        [_account_item(21), _account_item(25)],
    )

    first = list_fiscal_position_account_mappings(port, _request(limit=1))
    assert first["items"] == [_account_item(21)]
    assert first["has_more"] is True
    assert first["next_cursor"]
    assert port.calls == [{"fiscal_position_id": 9, "after_id": None, "limit": 2}]

    second = read_core_object(
        "fiscal_position.account_mapping.list",
        port,
        _request(limit=1, cursor=first["next_cursor"]),
    )
    assert second == {
        "items": [_account_item(25)],
        "has_more": False,
        "next_cursor": None,
    }
    assert port.calls[-1]["after_id"] == 21

    with pytest.raises(CoreObjectReadError) as caught:
        read_core_object(
            "fiscal_position.account_mapping.list",
            port,
            _request(fiscal_position_id=10, limit=1, cursor=first["next_cursor"]),
        )
    assert caught.value.code == "invalid_cursor"


def test_tax_mapping_pages_by_source_tax_and_exposes_remove_all_state() -> None:
    port = PagePort(
        "fiscal_position.tax_mapping.list",
        [_tax_item(11, 31, 32), _tax_item(12, 31)],
    )
    first = list_fiscal_position_tax_mappings(port, _request(limit=1))
    assert first == {
        "items": [_tax_item(11, 31, 32)],
        "has_more": True,
        "next_cursor": first["next_cursor"],
        "removes_all_taxes": False,
    }
    second = list_fiscal_position_tax_mappings(
        port, _request(limit=1, cursor=first["next_cursor"])
    )
    assert second == {
        "items": [_tax_item(12, 31)],
        "has_more": False,
        "next_cursor": None,
        "removes_all_taxes": False,
    }

    empty = list_fiscal_position_tax_mappings(
        PagePort(
            "fiscal_position.tax_mapping.list",
            [],
            removes_all_taxes=True,
        ),
        _request(),
    )
    assert empty == {
        "items": [],
        "has_more": False,
        "next_cursor": None,
        "removes_all_taxes": True,
    }


def _load_schema(name: str) -> dict[str, Any]:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def _validator(name: str) -> Draft202012Validator:
    resources: dict[str, Resource[Any]] = {}
    for shared_name in ("request.schema.json", "response.schema.json"):
        schema = _load_schema(shared_name)
        resource = Resource.from_contents(schema)
        resources[shared_name] = resource
        resources[schema["$id"]] = resource
    return Draft202012Validator(
        _load_schema(name),
        registry=Registry().with_resources(resources.items()),
        format_checker=FormatChecker(),
    )


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_schemas_are_closed_and_accept_exact_success_data(capability_id: str) -> None:
    request_name = f"{capability_id}.request.schema.json"
    response_name = f"{capability_id}.response.schema.json"
    Draft202012Validator.check_schema(_load_schema(request_name))
    Draft202012Validator.check_schema(_load_schema(response_name))
    _validator(request_name).validate(_request())
    data = (
        {
            "items": [_account_item(21)],
            "has_more": False,
            "next_cursor": None,
        }
        if capability_id == "fiscal_position.account_mapping.list"
        else {
            "items": [_tax_item(11, 31)],
            "has_more": False,
            "next_cursor": None,
            "removes_all_taxes": False,
        }
    )
    response = success_document(
        capability_id,
        data,
        request_id=REQUEST_ID,
        database="odoo_cli_v4_dev",
        company_id=7,
        user_id=42,
        model=(
            "account.fiscal.position.account"
            if capability_id == "fiscal_position.account_mapping.list"
            else "account.fiscal.position"
        ),
        record_ids=[21],
    )
    _validator(response_name).validate(response)
    invalid = deepcopy(response)
    invalid["data"]["unexpected"] = True
    with pytest.raises(ValidationError):
        _validator(response_name).validate(invalid)


@pytest.fixture(autouse=True)
def _fake_odoo_expression(monkeypatch: pytest.MonkeyPatch) -> None:
    def and_domains(domains: list[list[Any]]) -> list[Any]:
        return [term for domain in domains for term in domain]

    odoo = ModuleType("odoo")
    odoo.__path__ = []  # type: ignore[attr-defined]
    osv = ModuleType("odoo.osv")
    osv.expression = SimpleNamespace(AND=and_domains)  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "odoo", odoo)
    monkeypatch.setitem(sys.modules, "odoo.osv", osv)


def _relation_id(value: Any) -> Any:
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return value[0]
    return value


def _matches(row: dict[str, Any], domain: list[tuple[str, str, Any]]) -> bool:
    for field, operator, expected in domain:
        actual = _relation_id(row[field])
        if operator == "=" and actual != expected:
            return False
        if operator == ">" and not actual > expected:
            return False
        if operator == "in" and actual not in expected:
            return False
        if operator == "child_of" and actual not in expected:
            return False
    return True


class Model:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self.calls: list[tuple[Any, ...]] = []

    def with_context(self, **context: Any) -> Model:
        self.calls.append(("with_context", context))
        return self

    def has_access(self, operation: str) -> bool:
        self.calls.append(("has_access", operation))
        return operation == "read"

    def search_count(self, domain: list[Any], *, limit: int = 1) -> int:
        self.calls.append(("search_count", domain, limit))
        return min(limit, sum(_matches(row, domain) for row in self.rows))

    def search_read(
        self,
        domain: list[Any],
        *,
        fields: list[str],
        limit: int,
        order: str,
    ) -> list[dict[str, Any]]:
        self.calls.append(("search_read", domain, fields, limit, order))
        assert order == "id"
        rows = sorted(
            (row for row in self.rows if _matches(row, domain)),
            key=lambda row: row["id"],
        )[:limit]
        return [{field: row[field] for field in fields} for row in rows]

    def sudo(self, *_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("fiscal-position mapping reads must never sudo")


class User:
    def __init__(self) -> None:
        self.groups: list[str] = []

    def has_group(self, group: str) -> bool:
        self.groups.append(group)
        return group == "account.group_account_readonly"


class Env:
    uid = 42

    def __init__(self, models: dict[str, Model]) -> None:
        self.models = models
        self.registry = SimpleNamespace(get=models.get)
        self.user = User()

    def __getitem__(self, model_name: str) -> Model:
        return self.models[model_name]


class Failure(RuntimeError):
    def __init__(self, code: str, message: str, *, exit_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


def _runtime_fixture(*, empty_taxes: bool = False) -> Env:
    company = [7, "Demo Company"]
    fiscal_position = {
        "id": 9,
        "company_id": company,
        "tax_ids": [] if empty_taxes else [31, 32],
    }
    accounts = [
        {"id": 101, "code": "4000", "name": "Sales", "company_ids": [7]},
        {"id": 201, "code": "4100", "name": "Mapped sales", "company_ids": [7]},
        {"id": 102, "code": "5000", "name": "Costs", "company_ids": [7]},
        {"id": 202, "code": "5100", "name": "Mapped costs", "company_ids": [7]},
    ]
    mappings = [
        {
            "id": 21,
            "position_id": [9, "Domestic"],
            "company_id": company,
            "account_src_id": [101, "Sales"],
            "account_dest_id": [201, "Mapped sales"],
        },
        {
            "id": 25,
            "position_id": [9, "Domestic"],
            "company_id": company,
            "account_src_id": [102, "Costs"],
            "account_dest_id": [202, "Mapped costs"],
        },
    ]
    taxes = [
        {"id": 11, "name": "Source 11", "company_id": company, "original_tax_ids": []},
        {"id": 12, "name": "Source 12", "company_id": company, "original_tax_ids": []},
        {"id": 31, "name": "Destination 31", "company_id": company, "original_tax_ids": [11, 12]},
        {"id": 32, "name": "Destination 32", "company_id": company, "original_tax_ids": [11]},
    ]
    return Env(
        {
            "res.company": Model([{"id": 7}]),
            "account.fiscal.position": Model([fiscal_position]),
            "account.fiscal.position.account": Model(mappings),
            "account.account": Model(accounts),
            "account.tax": Model(taxes),
        }
    )


def _dispatch(
    env: Env, capability_id: str, *, after_id: int | None = None, limit: int = 3
) -> dict[str, Any]:
    return runtime.dispatch(
        env,
        {
            "capability_id": capability_id,
            "company_id": 7,
            "parameters": {
                "fiscal_position_id": 9,
                "after_id": after_id,
                "limit": limit,
            },
        },
        7,
        failure_type=Failure,
    )


def test_runtime_account_mapping_is_company_bound_and_id_ordered() -> None:
    env = _runtime_fixture()
    page = _dispatch(env, "fiscal_position.account_mapping.list", limit=2)

    assert page["items"] == [
        {
            "id": 21,
            "company_id": 7,
            "source_account": {"id": 101, "code": "4000", "name": "Sales"},
            "destination_account": {
                "id": 201,
                "code": "4100",
                "name": "Mapped sales",
            },
        },
        {
            "id": 25,
            "company_id": 7,
            "source_account": {"id": 102, "code": "5000", "name": "Costs"},
            "destination_account": {
                "id": 202,
                "code": "5100",
                "name": "Mapped costs",
            },
        },
    ]
    mapping_call = next(
        call
        for call in env.models["account.fiscal.position.account"].calls
        if call[0] == "search_read"
    )
    assert ("position_id", "=", 9) in mapping_call[1]
    assert ("company_id", "=", 7) in mapping_call[1]
    assert mapping_call[3:] == (2, "id")
    assert env.user.groups == ["account.group_account_readonly"]


def test_runtime_tax_mapping_uses_destination_original_tax_relation() -> None:
    env = _runtime_fixture()
    page = _dispatch(env, "fiscal_position.tax_mapping.list")

    assert page["items"] == [_tax_item(11, 31, 32), _tax_item(12, 31)]
    assert page["removes_all_taxes"] is False
    assert _dispatch(
        env, "fiscal_position.tax_mapping.list", after_id=11
    )["items"] == [_tax_item(12, 31)]
    assert _dispatch(
        _runtime_fixture(empty_taxes=True),
        "fiscal_position.tax_mapping.list",
    ) == {
        "user_id": 42,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "cursor_found": True,
        "items": [],
        "removes_all_taxes": True,
    }


def test_existing_fiscal_position_without_mapping_rows_is_a_verified_empty_page() -> None:
    env = _runtime_fixture()
    env.models["account.fiscal.position.account"].rows = []
    assert _dispatch(env, "fiscal_position.account_mapping.list")["items"] == []


@pytest.mark.parametrize(
    "capability_id",
    [
        "fiscal_position.account_mapping.list",
        "fiscal_position.tax_mapping.list",
    ],
)
@pytest.mark.parametrize("parent_state", ["missing", "other_company"])
def test_missing_or_cross_company_fiscal_position_is_not_found(
    capability_id: str, parent_state: str
) -> None:
    env = _runtime_fixture()
    if parent_state == "missing":
        env.models["account.fiscal.position"].rows = []
    else:
        env.models["account.fiscal.position"].rows[0]["company_id"] = [
            8,
            "Other Company",
        ]

    with pytest.raises(Failure) as caught:
        _dispatch(env, capability_id)

    assert caught.value.code == "record_not_found"
    assert caught.value.exit_code == 4


def test_runtime_models_acl_cursor_and_no_sudo_are_explicit() -> None:
    assert runtime._REQUIRED_MODELS["fiscal_position.account_mapping.list"] == (
        "res.company",
        "account.fiscal.position",
        "account.fiscal.position.account",
        "account.account",
    )
    assert runtime._REQUIRED_MODELS["fiscal_position.tax_mapping.list"] == (
        "res.company",
        "account.fiscal.position",
        "account.tax",
    )
    env = _runtime_fixture()
    stale = _dispatch(
        env, "fiscal_position.account_mapping.list", after_id=999
    )
    assert stale["cursor_found"] is False
    assert stale["items"] == []
    assert all(
        ("has_access", "read") in model.calls
        for name, model in env.models.items()
        if name in runtime._REQUIRED_MODELS["fiscal_position.account_mapping.list"]
    )
