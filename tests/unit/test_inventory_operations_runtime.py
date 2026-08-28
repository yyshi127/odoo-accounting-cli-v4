from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge import inventory_operations_runtime as inventory


class Failure(RuntimeError):
    def __init__(self, code: str, message: str, *, exit_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


def _raw_field(row: Any, field: str) -> Any:
    value = row
    for part in field.split("."):
        value = getattr(value, part)
    return value


def _value(value: Any) -> Any:
    return getattr(value, "id", value)


def _comparable(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return value


def _term(row: Any, term: tuple[str, str, Any]) -> bool:
    field, operator, expected = term
    raw = _raw_field(row, field)
    actual = _value(raw)
    if operator == "=":
        return actual == expected
    if operator == "in":
        return actual in expected
    if operator == "<":
        return _comparable(actual) < expected
    if operator == ">=":
        return _comparable(actual) >= expected
    if operator == "child_of":
        target = row if field == "id" else raw
        return _value(target) == expected or expected in getattr(
            target, "ancestor_ids", []
        )
    raise AssertionError(f"unsupported fake operator: {operator}")


def _matches(row: Any, domain: list[Any]) -> bool:
    index = 0
    while index < len(domain):
        token = domain[index]
        if token == "|":
            if not (_term(row, domain[index + 1]) or _term(row, domain[index + 2])):
                return False
            index += 3
        else:
            if not _term(row, token):
                return False
            index += 1
    return True


class Model:
    def __init__(
        self,
        rows: list[Any] | None = None,
        *,
        fields: set[str] | None = None,
        aggregates: list[tuple[Any, ...]] | None = None,
        access: bool = True,
    ) -> None:
        self.rows = rows or []
        self._fields = {name: object() for name in (fields or set())}
        self.aggregates = aggregates or []
        self.access = access
        self.calls: list[tuple[Any, ...]] = []

    def with_company(self, company_id: int) -> Model:
        self.calls.append(("with_company", company_id))
        return self

    def with_context(self, **context: Any) -> Model:
        self.calls.append(("with_context", context))
        return self

    def has_access(self, operation: str) -> bool:
        self.calls.append(("has_access", operation))
        return self.access

    def search_count(self, domain: list[Any], *, limit: int) -> int:
        self.calls.append(("search_count", deepcopy(domain), limit))
        return min(limit, sum(_matches(row, domain) for row in self.rows))

    def search(
        self, domain: list[Any], *, order: str | None = None, limit: int
    ) -> list[Any]:
        self.calls.append(("search", deepcopy(domain), order, limit))
        rows = [row for row in self.rows if _matches(row, domain)]
        if order == "id desc":
            rows.sort(key=lambda row: row.id, reverse=True)
        return rows[:limit]

    def _read_group(
        self,
        domain: list[Any],
        *,
        groupby: list[str],
        aggregates: list[str],
        order: str,
    ) -> list[tuple[Any, ...]]:
        self.calls.append(("_read_group", deepcopy(domain), groupby, aggregates, order))
        return self.aggregates


class Product(SimpleNamespace):
    def __init__(self, **values: Any) -> None:
        super().__init__(**values)
        self.calls: list[tuple[Any, ...]] = []

    def with_company(self, company_id: int) -> Product:
        self.calls.append(("with_company", company_id))
        return self

    def with_context(self, **context: Any) -> Product:
        self.calls.append(("with_context", context))
        return self


class User:
    def __init__(self, allowed: bool = True) -> None:
        self.allowed = allowed
        self.calls: list[str] = []

    def has_group(self, xml_id: str) -> bool:
        self.calls.append(xml_id)
        return self.allowed


class Registry:
    def __init__(self, models: dict[str, Model]) -> None:
        self.models = models

    def get(self, name: str) -> Model | None:
        return self.models.get(name)


class Env:
    uid = 5

    def __init__(self, models: dict[str, Model]) -> None:
        self.models = models
        self.registry = Registry(models)
        self.user = User()

    def __getitem__(self, name: str) -> Model:
        return self.models[name]


def fixture() -> tuple[Env, dict[str, Any]]:
    company = SimpleNamespace(id=1)
    uom = SimpleNamespace(id=1, display_name="Units")
    stock = SimpleNamespace(
        id=20,
        company_id=company,
        complete_name="WH/Stock",
        usage="internal",
        ancestor_ids=[],
    )
    customers = SimpleNamespace(
        id=30,
        company_id=False,
        complete_name="Customers",
        usage="customer",
        ancestor_ids=[],
    )
    picking_type = SimpleNamespace(
        id=4,
        company_id=company,
        code="outgoing",
        display_name="Delivery Orders",
    )
    partner = SimpleNamespace(id=40, display_name="Customer")
    transfer = SimpleNamespace(
        id=9,
        company_id=company,
        name="WH/OUT/00009",
        origin="SO001",
        state="assigned",
        picking_type_id=picking_type,
        scheduled_date=datetime(2026, 8, 28, 10, tzinfo=UTC),
        date_done=False,
        location_id=stock,
        location_dest_id=customers,
        partner_id=partner,
    )
    product = Product(
        id=50,
        company_id=False,
        default_code="TEST",
        display_name="Test product",
        uom_id=uom,
        is_storable=True,
        qty_available=5.0,
        free_qty=5.0,
        incoming_qty=0.0,
        outgoing_qty=0.0,
        virtual_available=5.0,
    )
    move = SimpleNamespace(
        id=19,
        company_id=company,
        reference="WH/OUT/00009",
        description_picking="Test product",
        state="assigned",
        date=datetime(2026, 8, 28, 9, tzinfo=UTC),
        picking_id=transfer,
        product_id=product,
        product_uom=uom,
        product_uom_qty=Decimal("5.0"),
        quantity=Decimal("2.0"),
        location_id=stock,
        location_dest_id=customers,
    )
    warehouse = SimpleNamespace(
        id=2,
        company_id=company,
        code="WH",
        name="Main Warehouse",
        lot_stock_id=stock,
    )
    models = {
        "res.company": Model([company]),
        "stock.picking": Model([transfer], fields=set(inventory._PICKING_FIELDS)),
        "stock.picking.type": Model(
            [picking_type], fields={"company_id", "code", "display_name"}
        ),
        "stock.location": Model(
            [stock, customers], fields={"company_id", "complete_name", "usage"}
        ),
        "res.partner": Model([partner], fields={"display_name"}),
        "stock.move": Model([move], fields=set(inventory._MOVE_FIELDS)),
        "product.product": Model(
            [product],
            fields=set(inventory._PRODUCT_FIELDS | inventory._AVAILABILITY_FIELDS),
        ),
        "uom.uom": Model([uom], fields={"display_name"}),
        "stock.quant": Model(
            fields=set(inventory._QUANT_FIELDS),
            aggregates=[(product, Decimal("5.0"), Decimal("2.0"))],
        ),
        "stock.warehouse": Model(
            [warehouse],
            fields={"company_id", "code", "name", "lot_stock_id"},
        ),
    }
    return Env(models), {
        "company": company,
        "stock": stock,
        "customers": customers,
        "picking_type": picking_type,
        "partner": partner,
        "transfer": transfer,
        "product": product,
        "move": move,
        "warehouse": warehouse,
    }


def dispatch(
    env: Env, capability_id: str, parameters: dict[str, Any]
) -> dict[str, Any]:
    return inventory.dispatch(
        env,
        {
            "capability_id": capability_id,
            "company_id": 1,
            "parameters": parameters,
        },
        1,
        failure_type=Failure,
    )


def test_transfer_search_uses_fixed_company_filters_and_id_cursor() -> None:
    env, _ = fixture()
    parameters = {
        "picking_type_id": 4,
        "partner_id": 40,
        "state": "assigned",
        "date_from": "2026-08-01",
        "date_to": "2026-08-31",
        "after": None,
        "limit": 101,
    }

    page = dispatch(env, "stock.transfer.search", parameters)

    assert inventory.ACTION == "accounting.inventory_operations.read"
    assert page["cursor_found"] is True
    assert page["items"][0]["operation_type"]["code"] == "outgoing"
    assert page["items"][0]["completed_date"] is None
    search_call = next(
        call for call in env.models["stock.picking"].calls if call[0] == "search"
    )
    assert search_call == (
        "search",
        [
            ("company_id", "=", 1),
            ("picking_type_id", "=", 4),
            ("partner_id", "=", 40),
            ("state", "=", "assigned"),
            ("scheduled_date", ">=", "2026-08-01 00:00:00"),
            ("scheduled_date", "<", "2026-09-01 00:00:00"),
        ],
        "id desc",
        101,
    )
    assert env.user.calls == ["account.group_account_readonly"]


def test_transfer_get_and_move_search_use_real_odoo19_fields() -> None:
    env, _ = fixture()
    transfer_page = dispatch(env, "stock.transfer.get", {"transfer_id": 9})
    assert transfer_page["items"][0]["name"] == "WH/OUT/00009"

    parameters = {
        "transfer_id": 9,
        "product_id": 50,
        "state": "assigned",
        "date_from": None,
        "date_to": None,
        "after": None,
        "limit": 10,
    }
    move_page = dispatch(env, "stock.move.search", parameters)
    item = move_page["items"][0]
    assert "name" not in item
    assert item["reference"] == "WH/OUT/00009"
    assert item["description_picking"] == "Test product"
    assert item["demand_quantity"] == "5"
    assert item["moved_quantity"] == "2"


def test_transfer_runtime_does_not_restrict_extended_operation_type_codes() -> None:
    env, records = fixture()
    records["picking_type"].code = "repair_operation"

    page = dispatch(env, "stock.transfer.get", {"transfer_id": 9})

    assert page["items"][0]["operation_type"]["code"] == "repair_operation"


def test_on_hand_uses_one_fixed_quant_aggregate_and_computes_available() -> None:
    env, _ = fixture()
    parameters = {"warehouse_id": 2, "location_id": 20, "product_id": 50}

    page = dispatch(env, "inventory.on_hand.summary", parameters)

    item = page["items"][0]
    assert item["warehouse"] == {"id": 2, "code": "WH", "name": "Main Warehouse"}
    assert item["location"] == {"id": 20, "name": "WH/Stock"}
    assert item["groups"] == [
        {
            "product": {"id": 50, "code": "TEST", "name": "Test product"},
            "uom": {"id": 1, "name": "Units"},
            "quantity": "5",
            "reserved_quantity": "2",
            "available_quantity": "3",
        }
    ]
    aggregate_call = next(
        call for call in env.models["stock.quant"].calls if call[0] == "_read_group"
    )
    assert aggregate_call == (
        "_read_group",
        [
            ("company_id", "=", 1),
            ("location_id.usage", "=", "internal"),
            ("location_id", "child_of", 20),
            ("location_id", "child_of", 20),
            ("product_id", "=", 50),
        ],
        ["product_id"],
        ["quantity:sum", "reserved_quantity:sum"],
        "product_id asc",
    )


def test_availability_uses_native_product_fields_with_location_context() -> None:
    env, records = fixture()

    page = dispatch(
        env,
        "inventory.availability.inspect",
        {"product_id": 50, "warehouse_id": None, "location_id": 20},
    )

    item = page["items"][0]
    assert item["on_hand_quantity"] == "5"
    assert item["free_quantity"] == "5"
    assert item["warehouse"] is None
    assert records["product"].calls == [
        ("with_company", 1),
        (
            "with_context",
            {"allowed_company_ids": [1], "active_test": False, "location": 20},
        ),
    ]


def test_missing_cursor_scope_returns_empty_cursor_page() -> None:
    env, _ = fixture()
    parameters = {
        "picking_type_id": None,
        "partner_id": None,
        "state": None,
        "date_from": None,
        "date_to": None,
        "after": 404,
        "limit": 10,
    }

    page = dispatch(env, "stock.transfer.search", parameters)

    assert page["cursor_found"] is False
    assert page["items"] == []
    assert not any(call[0] == "search" for call in env.models["stock.picking"].calls)


def test_runtime_gates_account_readonly_and_every_actual_model_acl() -> None:
    env, _ = fixture()
    env.models["stock.move"].access = False
    page = dispatch(
        env,
        "inventory.availability.inspect",
        {"product_id": 50, "warehouse_id": None, "location_id": None},
    )
    assert page["access_allowed"] is False
    assert page["items"] == []
    assert env.user.calls == ["account.group_account_readonly"]

    env, _ = fixture()
    env.user.allowed = False
    page = dispatch(
        env,
        "stock.move.search",
        {
            "transfer_id": None,
            "product_id": None,
            "state": None,
            "date_from": None,
            "date_to": None,
            "after": None,
            "limit": 10,
        },
    )
    assert page["access_allowed"] is False
    assert env.user.calls == ["account.group_account_readonly"]


def test_runtime_rejects_protocol_drift_field_drift_and_nonfinite_values() -> None:
    env, _ = fixture()
    invalid_payloads = [
        {
            "capability_id": "stock.move.search",
            "company_id": 1,
            "parameters": {"domain": []},
        },
        {
            "capability_id": "stock.transfer.search",
            "company_id": 1,
            "parameters": {
                "picking_type_id": None,
                "partner_id": None,
                "state": [],
                "date_from": None,
                "date_to": None,
                "after": None,
                "limit": 10,
            },
        },
        {
            "capability_id": "stock.transfer.get",
            "company_id": True,
            "parameters": {"transfer_id": 9},
        },
    ]
    for payload in invalid_payloads:
        with pytest.raises(Failure) as protocol:
            inventory.dispatch(
                env,
                payload,
                1,
                failure_type=Failure,
            )
        assert protocol.value.code == "bridge_protocol_error"

    env, _ = fixture()
    del env.models["stock.move"]._fields["description_picking"]
    with pytest.raises(Failure) as drift:
        dispatch(
            env,
            "stock.move.search",
            {
                "transfer_id": None,
                "product_id": None,
                "state": None,
                "date_from": None,
                "date_to": None,
                "after": None,
                "limit": 10,
            },
        )
    assert drift.value.code == "odoo_runtime_error"

    env, records = fixture()
    env.models["stock.quant"].aggregates = [
        (records["product"], Decimal("NaN"), Decimal(0))
    ]
    with pytest.raises(Failure) as nonfinite:
        dispatch(
            env,
            "inventory.on_hand.summary",
            {"warehouse_id": None, "location_id": None, "product_id": None},
        )
    assert nonfinite.value.code == "odoo_runtime_error"
