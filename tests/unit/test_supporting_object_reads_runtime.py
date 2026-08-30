from __future__ import annotations

import sys
from decimal import Decimal
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge import core_object_reads as bridge
from odoo_accounting_cli_v4.bridge import core_object_reads_runtime as runtime

CAPABILITY_IDS = frozenset(
    {
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
    }
)


@pytest.fixture(autouse=True)
def _fake_odoo_expression(monkeypatch: pytest.MonkeyPatch) -> None:
    def and_domains(domains: list[list[Any]]) -> list[Any]:
        nonempty = [domain for domain in domains if domain]
        return ["&"] * max(0, len(nonempty) - 1) + [
            item for domain in nonempty for item in domain
        ]

    odoo = ModuleType("odoo")
    odoo.__path__ = []  # type: ignore[attr-defined]
    osv = ModuleType("odoo.osv")
    osv.expression = SimpleNamespace(AND=and_domains)  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "odoo", odoo)
    monkeypatch.setitem(sys.modules, "odoo.osv", osv)


class Failure(RuntimeError):
    def __init__(self, code: str, message: str, *, exit_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


class Model:
    def __init__(
        self,
        name: str,
        rows: list[dict[str, Any]] | None = None,
        *,
        access: bool = True,
        search_count: int = 1,
    ) -> None:
        self.name = name
        self.rows = rows or []
        self.access = access
        self.search_count_result = search_count
        self.calls: list[tuple[Any, ...]] = []

    def with_context(self, **context: Any) -> Model:
        self.calls.append(("with_context", context))
        return self

    def has_access(self, operation: str) -> bool:
        self.calls.append(("has_access", operation))
        return self.access

    def search_count(self, domain: list[Any], *, limit: int | None = None) -> int:
        self.calls.append(("search_count", domain, limit))
        return self.search_count_result

    def search_read(
        self,
        domain: list[Any],
        *,
        fields: list[str],
        limit: int | None = None,
        order: str | None = None,
    ) -> list[dict[str, Any]]:
        self.calls.append(("search_read", domain, fields, limit, order))
        rows = self.rows[:limit] if limit is not None else self.rows
        return [{field: row[field] for field in fields} for row in rows]

    def sudo(self, *_args: Any, **_kwargs: Any) -> None:
        raise AssertionError(f"supporting-object runtime must not sudo {self.name}")


class Registry:
    def __init__(self, models: dict[str, Model]) -> None:
        self.models = models

    def get(self, name: str) -> Model | None:
        return self.models.get(name)


class User:
    def __init__(self, allowed: bool = True) -> None:
        self.allowed = allowed
        self.calls: list[str] = []

    def has_group(self, xml_id: str) -> bool:
        self.calls.append(xml_id)
        return self.allowed


class Env:
    uid = 5

    def __init__(self, models: dict[str, Model], *, group_allowed: bool = True) -> None:
        self.models = models
        self.registry = Registry(models)
        self.user = User(group_allowed)

    def __getitem__(self, name: str) -> Model:
        return self.models[name]


class Client:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def invoke(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((action, payload))
        return {
            "user_id": 5,
            "company_visible": True,
            "module_installed": True,
            "access_allowed": True,
            "cursor_found": True,
            "items": [],
        }


def _search_parameters(capability_id: str) -> dict[str, Any]:
    parameters = {
        "asset.group.search": {"query": None},
        "report.budget_definition.search": {"query": None},
        "report.budget_item.search": {
            "budget_id": None,
            "account_id": None,
            "date_from": None,
            "date_to": None,
        },
        "tax.unit.search": {
            "query": None,
            "country_id": None,
            "main_company_only": False,
        },
        "account.return.account_status.search": {
            "return_id": None,
            "account_id": None,
            "statuses": None,
        },
    }[capability_id]
    return {**parameters, "after_id": None, "limit": 101}


def _gate_env(capability_id: str, *, access: bool = True) -> Env:
    required_models = runtime._REQUIRED_MODELS[capability_id]
    primary_name = runtime._SUPPORTING_MODELS[
        runtime._SUPPORTING_OBJECT_KINDS[capability_id]
    ]
    models = {name: Model(name) for name in required_models}
    models["res.company"].search_count_result = 1
    models[primary_name].rows = []
    models[primary_name].access = access
    return Env(models)


def test_bridge_and_runtime_allowlist_exact_supporting_batch() -> None:
    assert CAPABILITY_IDS <= bridge.CAPABILITY_IDS
    assert CAPABILITY_IDS <= runtime.CAPABILITY_IDS
    client = Client()
    port = bridge.OdooCoreObjectReadPort(client)

    for capability_id in sorted(CAPABILITY_IDS):
        page = port.read(
            capability_id=capability_id,
            company_id=7,
            parameters={},
        )
        assert page["items"] == []
        assert port.user_id == 5
        assert client.calls[-1][0] == runtime.ACTION
        assert client.calls[-1][1]["capability_id"] == capability_id


@pytest.mark.parametrize(
    ("capability_id", "scope_term", "filter_terms"),
    [
        (
            "asset.group.search",
            ("company_id", "=", 7),
            (("name", "ilike", "Fleet"),),
        ),
        (
            "report.budget_definition.search",
            ("company_id", "=", 7),
            (("name", "ilike", "FY27"),),
        ),
        (
            "report.budget_item.search",
            ("budget_id.company_id", "=", 7),
            (
                ("budget_id", "=", 21),
                ("account_id", "=", 31),
                ("date", ">=", "2027-01-01"),
                ("date", "<=", "2027-12-31"),
            ),
        ),
        (
            "tax.unit.search",
            ("company_ids", "in", [7]),
            (
                ("name", "ilike", "Group VAT"),
                ("country_id", "=", 156),
                ("main_company_id", "=", 7),
            ),
        ),
        (
            "account.return.account_status.search",
            ("audit_id.company_id", "=", 7),
            (
                ("audit_id", "=", 41),
                ("account_id", "=", 31),
                ("status", "in", ["todo", "anomaly"]),
            ),
        ),
    ],
)
def test_supporting_searches_use_exact_company_scope_and_filters(
    capability_id: str,
    scope_term: tuple[Any, ...],
    filter_terms: tuple[tuple[Any, ...], ...],
) -> None:
    model_name = runtime._SUPPORTING_MODELS[
        runtime._SUPPORTING_OBJECT_KINDS[capability_id]
    ]
    model = Model(model_name, search_count=1)
    env = Env({model_name: model})
    parameters = {
        "asset.group.search": {"query": "Fleet"},
        "report.budget_definition.search": {"query": "FY27"},
        "report.budget_item.search": {
            "budget_id": 21,
            "account_id": 31,
            "date_from": "2027-01-01",
            "date_to": "2027-12-31",
        },
        "tax.unit.search": {
            "query": "Group VAT",
            "country_id": 156,
            "main_company_only": True,
        },
        "account.return.account_status.search": {
            "return_id": 41,
            "account_id": 31,
            "statuses": ["todo", "anomaly"],
        },
    }[capability_id]
    rows, cursor_found = runtime._supporting_object_rows(
        env,
        capability_id,
        {**parameters, "after_id": None, "limit": 101},
        7,
    )

    assert rows == []
    assert cursor_found is True
    assert ("with_context", {"active_test": False, "allowed_company_ids": [7]}) in (
        model.calls
    )
    domain = next(call[1] for call in model.calls if call[0] == "search_read")
    assert scope_term in domain
    for term in filter_terms:
        assert term in domain


def test_supporting_cursor_is_bound_to_the_filtered_company_domain() -> None:
    model = Model("account.asset.group", search_count=0)
    env = Env({"account.asset.group": model})
    parameters = {"query": "Fleet", "after_id": 12, "limit": 101}

    rows, cursor_found = runtime._supporting_object_rows(
        env, "asset.group.search", parameters, 7
    )

    assert rows == []
    assert cursor_found is False
    boundary = next(call[1] for call in model.calls if call[0] == "search_count")
    assert ("company_id", "=", 7) in boundary
    assert ("name", "ilike", "Fleet") in boundary
    assert ("id", "=", 12) in boundary
    assert not any(call[0] == "search_read" for call in model.calls)


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    [
        ("asset.group.get", {"asset_group_id": 999}),
        (
            "report.budget_definition.get",
            {"budget_definition_id": 999},
        ),
        ("report.budget_item.get", {"budget_item_id": 999}),
        ("tax.unit.get", {"tax_unit_id": 999}),
        (
            "account.return.account_status.get",
            {"account_status_id": 999},
        ),
    ],
)
def test_supporting_get_missing_returns_a_verified_empty_page(
    capability_id: str, parameters: dict[str, Any]
) -> None:
    env = _gate_env(capability_id)
    page = runtime.dispatch(
        env,
        {
            "capability_id": capability_id,
            "company_id": 7,
            "parameters": parameters,
        },
        7,
        failure_type=Failure,
    )

    assert page == {
        "user_id": 5,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "cursor_found": True,
        "items": [],
    }


def test_supporting_read_uses_accounting_group_and_model_read_acl() -> None:
    env = _gate_env("asset.group.search", access=False)
    page = runtime.dispatch(
        env,
        {
            "capability_id": "asset.group.search",
            "company_id": 7,
            "parameters": _search_parameters("asset.group.search"),
        },
        7,
        failure_type=Failure,
    )

    assert page["access_allowed"] is False
    assert page["items"] == []
    assert env.user.calls == ["account.group_account_readonly"]
    assert ("has_access", "read") in env["account.asset.group"].calls
    assert not any(
        call[0] == "search_read" for call in env["account.asset.group"].calls
    )


def test_supporting_normalization_is_minimal_company_safe_and_decimal_exact() -> None:
    models = {
        "res.country": Model(
            "res.country", [{"id": 156, "code": "CN", "name": "China"}]
        ),
        "account.report.budget": Model(
            "account.report.budget",
            [{"id": 21, "name": "FY27", "company_id": [7, "Company"]}],
        ),
        "account.account": Model(
            "account.account",
            [
                {
                    "id": 31,
                    "code": "660000",
                    "name": "Expense",
                    "company_ids": [7],
                }
            ],
        ),
        "account.return": Model(
            "account.return",
            [{"id": 41, "name": "Audit 2027", "company_id": [7, "Company"]}],
        ),
    }
    env = Env(models)

    assert runtime._normalize_supporting_objects(
        env,
        "asset.group.search",
        [
            {
                "id": 11,
                "name": False,
                "company_id": [7, "Company"],
                "count_linked_assets": 2,
            }
        ],
        7,
    ) == [
        {
            "id": 11,
            "name": None,
            "company_id": 7,
            "linked_asset_count": 2,
        }
    ]
    assert runtime._normalize_supporting_objects(
        env,
        "report.budget_definition.get",
        [
            {
                "id": 21,
                "name": "FY27",
                "sequence": 10,
                "company_id": [7, "Company"],
                "item_ids": [51, 52],
            }
        ],
        7,
    ) == [
        {
            "id": 21,
            "name": "FY27",
            "sequence": 10,
            "company_id": 7,
            "item_count": 2,
        }
    ]
    assert runtime._normalize_supporting_objects(
        env,
        "report.budget_item.search",
        [
            {
                "id": 51,
                "budget_id": [21, "FY27"],
                "account_id": [31, "Expense"],
                "amount": Decimal("1200.5000"),
                "date": "2027-01-01",
            }
        ],
        7,
    ) == [
        {
            "id": 51,
            "company_id": 7,
            "budget_definition": {"id": 21, "name": "FY27"},
            "account": {"id": 31, "code": "660000", "name": "Expense"},
            "amount": "1200.5",
            "date": "2027-01-01",
        }
    ]
    assert runtime._normalize_supporting_objects(
        env,
        "tax.unit.get",
        [
            {
                "id": 61,
                "name": "China VAT Group",
                "country_id": [156, "China"],
                "vat": "CN-VAT-61",
                "company_ids": [7, 8],
                "main_company_id": [8, "Other Company"],
                "fpos_synced": True,
            }
        ],
        7,
    ) == [
        {
            "id": 61,
            "company_id": 7,
            "name": "China VAT Group",
            "country": {"id": 156, "code": "CN", "name": "China"},
            "vat": "CN-VAT-61",
            "is_main_company": False,
            "fpos_synced": True,
        }
    ]
    assert runtime._normalize_supporting_objects(
        env,
        "account.return.account_status.get",
        [
            {
                "id": 71,
                "audit_id": [41, "Audit 2027"],
                "account_id": [31, "Expense"],
                "status": False,
            }
        ],
        7,
    ) == [
        {
            "id": 71,
            "company_id": 7,
            "return": {"id": 41, "name": "Audit 2027"},
            "account": {"id": 31, "code": "660000", "name": "Expense"},
            "status": None,
        }
    ]
    for model in models.values():
        if model.calls:
            assert (
                "with_context",
                {"active_test": False, "allowed_company_ids": [7]},
            ) in model.calls


def test_tax_unit_does_not_expose_member_company_details() -> None:
    country = Model("res.country", [{"id": 156, "code": "CN", "name": "China"}])
    env = Env({"res.country": country})
    item = runtime._normalize_supporting_objects(
        env,
        "tax.unit.search",
        [
            {
                "id": 61,
                "name": "China VAT Group",
                "country_id": [156, "China"],
                "vat": "CN-VAT-61",
                "company_ids": [7, 8, 9],
                "main_company_id": [8, "Hidden Company"],
                "fpos_synced": False,
            }
        ],
        7,
    )[0]

    assert set(item) == {
        "id",
        "company_id",
        "name",
        "country",
        "vat",
        "is_main_company",
        "fpos_synced",
    }
    assert item["company_id"] == 7
    assert "Hidden Company" not in repr(item)


def test_tax_unit_normalizes_missing_vat_to_null() -> None:
    country = Model("res.country", [{"id": 156, "code": "CN", "name": "China"}])
    env = Env({"res.country": country})

    item = runtime._normalize_supporting_objects(
        env,
        "tax.unit.get",
        [
            {
                "id": 61,
                "name": "China VAT Group",
                "country_id": [156, "China"],
                "vat": False,
                "company_ids": [7, 8],
                "main_company_id": [7, "Company"],
                "fpos_synced": True,
            }
        ],
        7,
    )[0]

    assert item["vat"] is None


def test_runtime_parameter_contract_rejects_null_main_company_flag_and_bad_status() -> (
    None
):
    valid_tax = _search_parameters("tax.unit.search")
    valid_status = _search_parameters("account.return.account_status.search")
    assert runtime._valid_parameters("tax.unit.search", valid_tax)
    assert runtime._valid_parameters(
        "account.return.account_status.search", valid_status
    )
    assert not runtime._valid_parameters(
        "tax.unit.search", {**valid_tax, "main_company_only": None}
    )
    assert not runtime._valid_parameters(
        "account.return.account_status.search",
        {**valid_status, "statuses": ["closed"]},
    )
