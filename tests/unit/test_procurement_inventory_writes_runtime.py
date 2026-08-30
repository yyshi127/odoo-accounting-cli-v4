from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge import core_writes_runtime as runtime

CAPABILITIES = (
    "purchase.order.bill.create",
    "purchase_bill.match",
    "purchase_bill.lines.unmatch",
)


class Failure(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        exit_code: int,
        retryable: bool,
        details: dict[str, Any],
    ) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code
        self.retryable = retryable
        self.details = details


class Records(list[Any]):
    @property
    def ids(self) -> list[int]:
        return [record.id for record in self]

    def write(self, values: dict[str, Any]) -> None:
        for record in self:
            for name, value in values.items():
                setattr(record, name, value)


def relation(record_id: int, **values: Any) -> SimpleNamespace:
    return SimpleNamespace(id=record_id, **values)


def bill_line(line_id: int, purchase_line: Any = False) -> SimpleNamespace:
    return SimpleNamespace(
        id=line_id,
        reconciled=False,
        purchase_line_id=purchase_line,
    )


class Bill:
    _name = "account.move"

    def __init__(self, lines: list[Any], *, state: str = "draft") -> None:
        self.id = 81
        self.name = "BILL/81"
        self.state = state
        self.company_id = relation(7)
        self.move_type = "in_invoice"
        self.partner_id = relation(31, commercial_partner_id=relation(31))
        self.line_ids = Records(lines)
        self.invoice_line_ids = self.line_ids

    def __len__(self) -> int:
        return 1


def purchase_line(line_id: int, order: Any) -> SimpleNamespace:
    return relation(
        line_id,
        display_type=False,
        product_qty=1,
        qty_to_invoice=0,
        order_id=order,
        product_id=relation(51),
    )


def test_procurement_capabilities_keep_invoice_only_scope() -> None:
    assert set(CAPABILITIES) <= runtime.CAPABILITIES
    assert {runtime._GROUPS[item] for item in CAPABILITIES} == {
        "account.group_account_invoice"
    }
    assert all("stock.picking" not in runtime._MODELS[item] for item in CAPABILITIES)


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    [
        ("purchase.order.bill.create", {"order_id": 41}),
        (
            "purchase_bill.match",
            {
                "bill_id": 81,
                "pairs": [{"purchase_line_id": 61, "bill_line_id": 71}],
            },
        ),
        (
            "purchase_bill.lines.unmatch",
            {"bill_id": 81, "bill_line_ids": [71]},
        ),
    ],
)
def test_parameters_and_deterministic_keys(
    capability_id: str, parameters: dict[str, Any]
) -> None:
    assert runtime._valid_parameters(capability_id, parameters)
    key = runtime._deterministic_key(capability_id, parameters, 7)
    assert isinstance(key, str) and key.startswith(f"{capability_id}:")


def test_bill_create_first_execution_and_replay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    order = relation(
        41,
        state="purchase",
        invoice_status="to invoice",
        action_create_invoice=lambda: None,
    )
    po_line = purchase_line(61, order)
    order.order_line = Records([po_line])
    linked_line = bill_line(71, po_line)
    bill = Bill([linked_line])
    linked_results = iter((Records(), bill))
    monkeypatch.setattr(runtime, "_search_one", lambda *_args, **_kwargs: order)
    monkeypatch.setattr(
        runtime, "_linked_purchase_bills", lambda *_args: next(linked_results)
    )

    result, replay = runtime._create_purchase_bill(
        object(), {"order_id": 41}, 7, Failure
    )
    assert replay is False
    assert result["model"] == "account.move"
    assert result["source_id"] == 41

    monkeypatch.setattr(runtime, "_linked_purchase_bills", lambda *_args: bill)
    result, replay = runtime._create_purchase_bill(
        object(), {"order_id": 41}, 7, Failure
    )
    assert replay is True
    assert result["id"] == 81


def test_bill_create_rejects_unconfirmed_order(monkeypatch: pytest.MonkeyPatch) -> None:
    order = relation(41, state="draft", invoice_status="to invoice")
    order.order_line = Records()
    monkeypatch.setattr(runtime, "_search_one", lambda *_args, **_kwargs: order)
    monkeypatch.setattr(runtime, "_linked_purchase_bills", lambda *_args: Records())

    with pytest.raises(Failure) as captured:
        runtime._create_purchase_bill(object(), {"order_id": 41}, 7, Failure)
    assert captured.value.code == "state_conflict"


class MatchRows:
    def __init__(self, purchase: Any, line: Any) -> None:
        self.purchase = purchase
        self.line = line

    def exists(self) -> MatchRows:
        return self

    def __len__(self) -> int:
        return 2

    def action_match_lines(self) -> None:
        self.line.purchase_line_id = self.purchase


class MatchModel:
    def __init__(self, purchase: Any, line: Any) -> None:
        self.purchase = purchase
        self.line = line

    def browse(self, ids: list[int]) -> MatchRows:
        assert ids == [self.purchase.id, -self.line.id]
        return MatchRows(self.purchase, self.line)


def test_match_first_execution_and_replay(monkeypatch: pytest.MonkeyPatch) -> None:
    order = relation(41, company_id=relation(7), state="purchase")
    purchase = purchase_line(61, order)
    line = bill_line(71)
    bill = Bill([line])
    monkeypatch.setattr(runtime, "_purchase_bill", lambda *_args: bill)
    monkeypatch.setattr(
        runtime, "_purchase_match_records", lambda *_args: [(purchase, line)]
    )
    monkeypatch.setattr(runtime, "_scoped", lambda *_args: MatchModel(purchase, line))
    parameters = {
        "bill_id": 81,
        "pairs": [{"purchase_line_id": 61, "bill_line_id": 71}],
    }

    result, replay = runtime._match_purchase_bill_lines(
        object(), parameters, 7, Failure
    )
    assert replay is False
    assert result["line_ids"] == [71]
    result, replay = runtime._match_purchase_bill_lines(
        object(), parameters, 7, Failure
    )
    assert replay is True
    assert result["source_id"] is None


def test_match_rejects_cross_company_purchase_line(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bill = Bill([bill_line(71)])
    order = relation(
        41,
        company_id=relation(8),
        state="purchase",
        partner_id=relation(
            31, commercial_partner_id=bill.partner_id.commercial_partner_id
        ),
    )
    purchase = purchase_line(61, order)
    purchase.product_id = relation(51)
    line = bill.invoice_line_ids[0]
    line.product_id = purchase.product_id
    monkeypatch.setattr(
        runtime,
        "_ensure_ids",
        lambda _env, model, *_args, **_kwargs: (
            Records([purchase]) if model == "purchase.order.line" else Records([line])
        ),
    )

    with pytest.raises(Failure) as captured:
        runtime._purchase_match_records(
            object(),
            bill,
            [{"purchase_line_id": 61, "bill_line_id": 71}],
            7,
            Failure,
        )
    assert captured.value.code == "state_conflict"


def test_unmatch_first_execution_and_replay(monkeypatch: pytest.MonkeyPatch) -> None:
    linked = relation(61)
    line = bill_line(71, linked)
    bill = Bill([line])
    monkeypatch.setattr(runtime, "_purchase_bill", lambda *_args: bill)
    monkeypatch.setattr(
        runtime, "_ensure_ids", lambda *_args, **_kwargs: Records([line])
    )
    parameters = {"bill_id": 81, "bill_line_ids": [71]}

    result, replay = runtime._unmatch_purchase_bill_lines(
        object(), parameters, 7, Failure
    )
    assert replay is False
    assert result["line_ids"] == [71]
    result, replay = runtime._unmatch_purchase_bill_lines(
        object(), parameters, 7, Failure
    )
    assert replay is True


def test_purchase_bill_requires_draft_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        runtime, "_search_one", lambda *_args, **_kwargs: Bill([], state="posted")
    )
    with pytest.raises(Failure) as captured:
        runtime._purchase_bill(object(), 81, 7, Failure)
    assert captured.value.code == "state_conflict"
