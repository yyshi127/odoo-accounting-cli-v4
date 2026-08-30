from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge import core_writes_runtime as writes


class Failure(RuntimeError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        exit_code: int,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code
        self.retryable = retryable
        self.details = details or {}


class Records(list[Any]):
    @property
    def ids(self) -> list[int]:
        return [record.id for record in self]

    @property
    def id(self) -> int | bool:
        return self[0].id if len(self) == 1 else False

    def __getattr__(self, name: str) -> Any:
        if len(self) != 1:
            raise AttributeError(name)
        return getattr(self[0], name)

    def filtered(self, predicate: Any) -> Records:
        return Records(record for record in self if predicate(record))

    def invalidate_recordset(self, _fields: list[str]) -> None:
        return None


class Move:
    def __init__(
        self,
        move_id: int,
        *,
        product_id: int = 51,
        quantity: str = "0",
        demand: str = "3",
        uom_id: int = 1,
        name: str = "Stock item",
        tracking: str = "none",
    ) -> None:
        self.id = move_id
        self.product_id = SimpleNamespace(id=product_id, tracking=tracking)
        self.has_tracking = tracking
        self.quantity = Decimal(quantity)
        self.product_uom_qty = Decimal(demand)
        self.product_uom = SimpleNamespace(id=uom_id)
        self.description_picking = name
        self.writes: list[dict[str, Any]] = []

    def write(self, values: dict[str, Any]) -> bool:
        assert set(values) == {"quantity"}
        self.writes.append(dict(values))
        self.quantity = values["quantity"]
        return True

    def sudo(self, *_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("stock moves must never sudo")


class Picking:
    def __init__(
        self,
        *,
        picking_id: int = 401,
        state: str = "draft",
        moves: Records | None = None,
        type_policy: str = "ask",
    ) -> None:
        self.id = picking_id
        self.name = "WH/INT/00401"
        self.display_name = self.name
        self.state = state
        self.company_id = SimpleNamespace(id=7)
        self.picking_type_id = SimpleNamespace(id=2, create_backorder=type_policy)
        self.location_id = SimpleNamespace(id=8)
        self.location_dest_id = SimpleNamespace(id=9)
        self.partner_id = SimpleNamespace(id=12)
        self.scheduled_date = False
        self.origin = "fixture"
        self.move_ids = moves or Records([Move(501)])
        self.calls: list[str] = []
        self.context: dict[str, Any] = {}
        self.validate_result: Any = True
        self.validation_completes = True

    def action_confirm(self) -> bool:
        self.calls.append("action_confirm")
        self.state = "confirmed"
        return True

    def action_assign(self) -> bool:
        self.calls.append("action_assign")
        self.state = "assigned"
        return True

    def do_unreserve(self) -> None:
        self.calls.append("do_unreserve")
        self.state = "confirmed"

    def action_cancel(self) -> bool:
        self.calls.append("action_cancel")
        self.state = "cancel"
        return True

    def with_context(self, **context: Any) -> Picking:
        self.context = dict(context)
        return self

    def button_validate(self) -> Any:
        self.calls.append("button_validate")
        if self.validation_completes:
            self.state = "done"
        return self.validate_result

    def invalidate_recordset(self, _fields: list[str]) -> None:
        return None

    def sudo(self, *_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("stock transfers must never sudo")


def _create_parameters() -> dict[str, Any]:
    return {
        "picking_type_id": 2,
        "location_id": 8,
        "location_dest_id": 9,
        "partner_id": 12,
        "scheduled_date": None,
        "origin": "CLI transfer",
        "moves": [
            {
                "product_id": 51,
                "name": "Stock item",
                "quantity": "3",
                "uom_id": 1,
            }
        ],
    }


def test_runtime_contracts_and_deterministic_keys_match_the_fixed_batch() -> None:
    expected_ids = {
        "sale.order.invoice.create",
        "stock.transfer.create",
        "stock.transfer.confirm",
        "stock.transfer.assign",
        "stock.transfer.quantities.set",
        "stock.transfer.validate",
        "stock.transfer.unreserve",
        "stock.transfer.cancel",
    }
    assert expected_ids <= writes.CAPABILITIES
    assert (
        writes._deterministic_key("sale.order.invoice.create", {"order_id": 101}, 7)
        == "sale.order.invoice.create:101"
    )
    assert (
        writes._deterministic_key("stock.transfer.create", _create_parameters(), 7)
        is None
    )
    assert (
        writes._deterministic_key(
            "stock.transfer.validate",
            {"transfer_id": 401, "backorder_policy": "cancel"},
            7,
        )
        == "stock.transfer.validate:401:cancel"
    )
    assert ("stock.move", "write") in writes._ACCESS["stock.transfer.quantities.set"]


def test_runtime_rejects_marker_injection_and_noncanonical_quantities() -> None:
    parameters = _create_parameters()
    assert writes._valid_parameters("stock.transfer.create", parameters, 7)
    assert not writes._valid_parameters(
        "stock.transfer.create", {**parameters, "origin": "ODACV4:forged"}, 7
    )
    assert not writes._valid_parameters(
        "stock.transfer.create",
        {
            **parameters,
            "moves": [{**parameters["moves"][0], "quantity": "3.0"}],
        },
        7,
    )
    assert writes._valid_parameters(
        "stock.transfer.quantities.set",
        {
            "transfer_id": 401,
            "lines": [
                {"move_id": 501, "quantity": "0"},
                {"move_id": 502, "quantity": "2.5"},
            ],
        },
        7,
    )


def test_sale_invoice_uses_the_native_single_order_path(monkeypatch: Any) -> None:
    order = SimpleNamespace(id=101, state="sale", invoice_status="to invoice")
    sale_line = SimpleNamespace(order_id=order)
    invoice_line = SimpleNamespace(sale_line_ids=Records([sale_line]))
    journal_line = SimpleNamespace(id=701, reconciled=False)
    invoice = SimpleNamespace(
        id=601,
        name=False,
        state="draft",
        company_id=SimpleNamespace(id=7),
        move_type="out_invoice",
        invoice_line_ids=Records([invoice_line]),
        line_ids=Records([journal_line]),
    )
    created = Records([invoice])
    calls: list[str] = []

    def create_invoices() -> Records:
        calls.append("_create_invoices")
        return created

    order._create_invoices = create_invoices
    linked = iter((Records(), created))
    monkeypatch.setattr(writes, "_search_one", lambda *_args, **_kwargs: order)
    monkeypatch.setattr(writes, "_linked_sale_invoices", lambda *_args: next(linked))

    result, replay = writes._create_sale_order_invoice(
        object(), {"order_id": 101}, 7, Failure
    )

    assert calls == ["_create_invoices"]
    assert replay is False
    assert result["model"] == "account.move"
    assert result["source_id"] == 101
    assert result["line_ids"] == [701]


def test_stock_create_uses_visible_markers_and_nested_draft_moves(
    monkeypatch: Any,
) -> None:
    parameters = _create_parameters()
    captured: dict[str, Any] = {}

    class Model:
        def create(self, values: dict[str, Any]) -> Picking:
            captured.update(values)
            command_values = values["move_ids"][0][2]
            picking = Picking(state="draft", moves=Records([Move(501)]))
            picking.origin = values["origin"]
            picking.scheduled_date = values.get("scheduled_date", False)
            picking.partner_id = SimpleNamespace(id=values["partner_id"])
            picking.move_ids[0].product_id = SimpleNamespace(
                id=command_values["product_id"], tracking="none"
            )
            picking.move_ids[0].product_uom_qty = command_values["product_uom_qty"]
            picking.move_ids[0].product_uom = SimpleNamespace(
                id=command_values["product_uom"]
            )
            picking.move_ids[0].description_picking = command_values[
                "description_picking"
            ]
            return picking

    monkeypatch.setattr(writes, "_existing_stock_transfer_for_key", lambda *_args: None)
    monkeypatch.setattr(
        writes, "_validate_stock_transfer_references", lambda *_args: None
    )
    monkeypatch.setattr(writes, "_scoped", lambda *_args: Model())

    result, replay = writes._create_stock_transfer(
        object(), parameters, 7, "caller-key", "ODACV4:parameters", Failure
    )

    assert replay is False
    assert result["state"] == "draft"
    assert captured["origin"].startswith("CLI transfer;ODACV4K:")
    assert captured["origin"].endswith(";ODACV4:parameters")
    assert "scheduled_date" not in captured
    assert captured["move_ids"][0][2]["product_uom_qty"] == Decimal(3)
    assert captured["move_ids"][0][2]["description_picking"] == "Stock item"
    assert "name" not in captured["move_ids"][0][2]
    assert "sudo" not in captured


@pytest.mark.parametrize(("compatible", "raises"), ((True, False), (False, True)))
def test_stock_create_uses_odoo_19_common_uom_reference(
    monkeypatch: Any, compatible: bool, raises: bool
) -> None:
    requested_uom = SimpleNamespace(id=1)
    product_uom = SimpleNamespace(
        _has_common_reference=lambda other: other is requested_uom and compatible
    )
    product = SimpleNamespace(id=51, uom_id=product_uom)

    def ensure_ids(_env: Any, model: str, *_args: Any, **_kwargs: Any) -> Records:
        if model == "product.product":
            return Records([product])
        if model == "uom.uom":
            return Records([requested_uom])
        return Records()

    monkeypatch.setattr(writes, "_ensure_ids", ensure_ids)
    if raises:
        with pytest.raises(Failure) as caught:
            writes._validate_stock_transfer_references(
                object(), _create_parameters(), 7, Failure
            )
        assert caught.value.code == "state_conflict"
    else:
        writes._validate_stock_transfer_references(
            object(), _create_parameters(), 7, Failure
        )


@pytest.mark.parametrize(
    ("capability_id", "state", "method", "target"),
    (
        ("stock.transfer.confirm", "draft", "action_confirm", "confirmed"),
        ("stock.transfer.assign", "confirmed", "action_assign", "assigned"),
        ("stock.transfer.unreserve", "assigned", "do_unreserve", "confirmed"),
        ("stock.transfer.cancel", "confirmed", "action_cancel", "cancel"),
    ),
)
def test_stock_transitions_call_only_the_fixed_native_action(
    monkeypatch: Any,
    capability_id: str,
    state: str,
    method: str,
    target: str,
) -> None:
    picking = Picking(state=state)
    monkeypatch.setattr(writes, "_stock_transfer", lambda *_args: picking)

    result, replay = writes._transition_stock_transfer(
        object(), capability_id, {"transfer_id": 401}, 7, Failure
    )

    assert replay is False
    assert picking.calls == [method]
    assert result["state"] == target


def test_quantities_write_odoo_19_stock_move_quantity_and_replay(
    monkeypatch: Any,
) -> None:
    move = Move(501, quantity="0")
    picking = Picking(state="assigned", moves=Records([move]))
    monkeypatch.setattr(writes, "_stock_transfer", lambda *_args: picking)
    monkeypatch.setattr(writes, "_ensure_ids", lambda *_args: Records([move]))
    parameters = {
        "transfer_id": 401,
        "lines": [{"move_id": 501, "quantity": "2.5"}],
    }

    first, first_replay = writes._set_stock_transfer_quantities(
        object(), parameters, 7, Failure
    )
    second, second_replay = writes._set_stock_transfer_quantities(
        object(), parameters, 7, Failure
    )

    assert move.writes == [{"quantity": Decimal("2.5")}]
    assert first["state"] == second["state"] == "assigned"
    assert first_replay is False
    assert second_replay is True


def test_validate_fixes_backorder_context_and_replays_done_state(
    monkeypatch: Any,
) -> None:
    picking = Picking(state="assigned", type_policy="ask")
    monkeypatch.setattr(writes, "_stock_transfer", lambda *_args: picking)
    parameters = {"transfer_id": 401, "backorder_policy": "cancel"}

    first, first_replay = writes._validate_stock_transfer(
        object(), parameters, 7, Failure
    )
    second, second_replay = writes._validate_stock_transfer(
        object(), parameters, 7, Failure
    )

    assert picking.calls == ["button_validate"]
    assert picking.context == {
        "skip_backorder": True,
        "button_validate_picking_ids": [401],
        "picking_ids_not_to_backorder": [401],
    }
    assert first["state"] == second["state"] == "done"
    assert first_replay is False
    assert second_replay is True


def test_validate_rejects_an_unhandled_odoo_action(monkeypatch: Any) -> None:
    picking = Picking(state="assigned")
    picking.validate_result = {"type": "ir.actions.act_window"}
    picking.validation_completes = False
    monkeypatch.setattr(writes, "_stock_transfer", lambda *_args: picking)

    with pytest.raises(Failure) as caught:
        writes._validate_stock_transfer(
            object(),
            {"transfer_id": 401, "backorder_policy": "create"},
            7,
            Failure,
        )

    assert caught.value.code == "state_conflict"


def test_validate_accepts_a_post_completion_odoo_action(monkeypatch: Any) -> None:
    picking = Picking(state="assigned")
    picking.validate_result = {"type": "ir.actions.report"}
    monkeypatch.setattr(writes, "_stock_transfer", lambda *_args: picking)

    result, replay = writes._validate_stock_transfer(
        object(),
        {"transfer_id": 401, "backorder_policy": "create"},
        7,
        Failure,
    )

    assert result["state"] == "done"
    assert replay is False


@pytest.mark.parametrize(
    ("type_policy", "backorder_policy"), (("never", "create"), ("always", "cancel"))
)
def test_validate_rejects_picking_type_policy_conflicts(
    monkeypatch: Any, type_policy: str, backorder_policy: str
) -> None:
    picking = Picking(state="assigned", type_policy=type_policy)
    monkeypatch.setattr(writes, "_stock_transfer", lambda *_args: picking)

    with pytest.raises(Failure) as caught:
        writes._validate_stock_transfer(
            object(),
            {"transfer_id": 401, "backorder_policy": backorder_policy},
            7,
            Failure,
        )

    assert caught.value.code == "state_conflict"
