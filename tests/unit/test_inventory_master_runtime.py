from __future__ import annotations

from copy import deepcopy

import pytest

from odoo_accounting_cli_v4.bridge.inventory_master_runtime import ACTION, dispatch


class Failure(RuntimeError):
    def __init__(self, code: str, message: str, *, exit_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


ROWS = {
    "product.category": {
        "id": 9,
        "name": "All",
        "complete_name": "All",
        "parent_id": False,
    },
    "stock.warehouse": {
        "id": 9,
        "name": "Main Warehouse",
        "code": "WH",
        "active": True,
        "company_id": [1, "My Company"],
        "reception_steps": "one_step",
        "delivery_steps": "ship_only",
    },
    "stock.location": {
        "id": 9,
        "name": "Stock",
        "complete_name": "WH/Stock",
        "active": True,
        "usage": "internal",
        "company_id": [1, "My Company"],
        "location_id": [3, "WH"],
        "warehouse_id": [2, "Main Warehouse"],
    },
    "stock.picking.type": {
        "id": 9,
        "name": "Receipts",
        "active": True,
        "code": "incoming",
        "sequence_code": "IN",
        "company_id": [1, "My Company"],
        "warehouse_id": [2, "Main Warehouse"],
        "default_location_src_id": [4, "Vendors"],
        "default_location_dest_id": [9, "WH/Stock"],
    },
    "stock.route": {
        "id": 9,
        "name": "Buy",
        "active": True,
        "sequence": 10,
        "company_id": False,
        "product_selectable": True,
        "product_categ_selectable": True,
        "warehouse_selectable": False,
        "warehouse_ids": [2],
    },
}


CASES = {
    "product.category.list": ("product.category", []),
    "warehouse.list": (
        "stock.warehouse",
        [("company_id", "=", 1), ("active", "=", True)],
    ),
    "stock.location.list": (
        "stock.location",
        [
            "|",
            ("company_id", "=", False),
            ("company_id", "=", 1),
            ("active", "=", True),
        ],
    ),
    "stock.operation_type.list": (
        "stock.picking.type",
        [("company_id", "=", 1), ("active", "=", True)],
    ),
    "stock.route.list": (
        "stock.route",
        [
            "|",
            ("company_id", "=", False),
            ("company_id", "=", 1),
            ("active", "=", True),
        ],
    ),
}


class Model:
    def __init__(
        self,
        name: str,
        row: dict | None = None,
        *,
        access: bool = True,
        fields: set[str] | None = None,
    ) -> None:
        self.name = name
        self.row = row
        self.access = access
        self._fields = {field: object() for field in (fields or set(row or {}))}
        self.search_count_calls: list[tuple[list, int | None]] = []
        self.search_read_calls: list[tuple[list, list[str], str, int]] = []
        self.companies: list[int] = []
        self.contexts: list[dict] = []

    def has_access(self, operation: str) -> bool:
        assert operation == "read"
        return self.access

    def with_company(self, company_id: int) -> Model:
        self.companies.append(company_id)
        return self

    def with_context(self, **context: object) -> Model:
        self.contexts.append(context)
        return self

    def search_count(self, domain: list, limit: int | None = None) -> int:
        self.search_count_calls.append((deepcopy(domain), limit))
        if self.name == "res.company":
            return 1
        if ("id", "=", 404) in domain:
            return 0
        return 1

    def search_read(
        self, domain: list, fields: list[str], *, order: str, limit: int
    ) -> list[dict]:
        self.search_read_calls.append((deepcopy(domain), fields, order, limit))
        return [] if self.row is None else [deepcopy(self.row)]


class User:
    def __init__(self, internal: bool = True) -> None:
        self.internal = internal

    def has_group(self, xml_id: str) -> bool:
        assert xml_id == "account.group_account_readonly"
        return self.internal


class Registry:
    def __init__(self, models: dict[str, Model]) -> None:
        self.models = models

    def get(self, name: str) -> object | None:
        return self.models.get(name)


class Env:
    uid = 5

    def __init__(self, target: str, *, access: bool = True) -> None:
        self.models = {
            "res.company": Model("res.company", fields={"id"}),
            target: Model(target, ROWS[target], access=access),
        }
        self.registry = Registry(self.models)
        self.user = User()

    def __getitem__(self, name: str) -> Model:
        return self.models[name]


@pytest.mark.parametrize(("capability_id", "case"), CASES.items())
def test_dispatch_uses_one_explicit_model_and_company_domain(
    capability_id: str, case: tuple[str, list]
) -> None:
    model_name, expected_domain = case
    env = Env(model_name)
    parameters = {
        **(
            {"parent_id": None}
            if capability_id == "product.category.list"
            else {"active": True}
        ),
        **(
            {"warehouse_id": None, "usage": None}
            if capability_id == "stock.location.list"
            else {}
        ),
        **(
            {"warehouse_id": None, "code": None}
            if capability_id == "stock.operation_type.list"
            else {}
        ),
        **({"warehouse_id": None} if capability_id == "stock.route.list" else {}),
        "after": None,
        "limit": 101,
    }

    page = dispatch(
        env,
        {"capability_id": capability_id, "company_id": 1, "parameters": parameters},
        1,
        failure_type=Failure,
    )

    assert ACTION == "accounting.inventory_master.read"
    assert page["user_id"] == 5
    assert page["access_allowed"] is True
    assert page["cursor_found"] is True
    assert page["items"][0]["id"] == 9
    model = env.models[model_name]
    assert model.search_read_calls[0][0] == expected_domain
    assert model.search_read_calls[0][2:] == ("id desc", 101)
    assert model.companies == [1]
    assert model.contexts == [{"allowed_company_ids": [1], "active_test": False}]


def test_cursor_must_still_be_in_the_same_fixed_scope() -> None:
    env = Env("stock.warehouse")
    page = dispatch(
        env,
        {
            "capability_id": "warehouse.list",
            "company_id": 1,
            "parameters": {"active": None, "after": 404, "limit": 10},
        },
        1,
        failure_type=Failure,
    )
    assert page["cursor_found"] is False
    assert page["items"] == []
    assert env.models["stock.warehouse"].search_read_calls == []


def test_acl_denial_returns_an_empty_gated_page() -> None:
    env = Env("stock.route", access=False)
    page = dispatch(
        env,
        {
            "capability_id": "stock.route.list",
            "company_id": 1,
            "parameters": {
                "active": True,
                "warehouse_id": None,
                "after": None,
                "limit": 10,
            },
        },
        1,
        failure_type=Failure,
    )
    assert page == {
        "user_id": 5,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": False,
        "cursor_found": True,
        "items": [],
    }


@pytest.mark.parametrize(
    "payload",
    [
        {"capability_id": "stock.rule.list", "company_id": 1, "parameters": {}},
        {
            "capability_id": "warehouse.list",
            "company_id": 2,
            "parameters": {"active": True, "after": None, "limit": 10},
        },
        {
            "capability_id": "warehouse.list",
            "company_id": 1,
            "parameters": {"active": True, "cursor": None, "limit": 10},
        },
    ],
)
def test_runtime_rejects_any_payload_outside_the_bridge_protocol(payload: dict) -> None:
    with pytest.raises(Failure) as exc_info:
        dispatch(Env("stock.warehouse"), payload, 1, failure_type=Failure)
    assert exc_info.value.code == "bridge_protocol_error"


@pytest.mark.parametrize(
    ("capability_id", "model_name", "parameters", "terms"),
    [
        (
            "product.category.list",
            "product.category",
            {"parent_id": 4, "after": None, "limit": 10},
            [("parent_id", "=", 4)],
        ),
        (
            "stock.location.list",
            "stock.location",
            {
                "active": None,
                "warehouse_id": 2,
                "usage": "internal",
                "after": None,
                "limit": 10,
            },
            [("warehouse_id", "=", 2), ("usage", "=", "internal")],
        ),
        (
            "stock.operation_type.list",
            "stock.picking.type",
            {
                "active": None,
                "warehouse_id": 2,
                "code": "incoming",
                "after": None,
                "limit": 10,
            },
            [("warehouse_id", "=", 2), ("code", "=", "incoming")],
        ),
        (
            "stock.route.list",
            "stock.route",
            {"active": None, "warehouse_id": 2, "after": None, "limit": 10},
            [("warehouse_ids", "in", [2])],
        ),
    ],
)
def test_runtime_translates_only_frozen_native_filters(
    capability_id: str,
    model_name: str,
    parameters: dict,
    terms: list,
) -> None:
    env = Env(model_name)
    dispatch(
        env,
        {"capability_id": capability_id, "company_id": 1, "parameters": parameters},
        1,
        failure_type=Failure,
    )
    domain = env.models[model_name].search_read_calls[0][0]
    for term in terms:
        assert term in domain
