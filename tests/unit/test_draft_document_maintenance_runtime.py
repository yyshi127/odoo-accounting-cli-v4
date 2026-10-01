from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from odoo_accounting_cli_v4 import cli
from odoo_accounting_cli_v4.bridge import core_writes_runtime as runtime
from odoo_accounting_cli_v4.capabilities import core_writes as public

CAPABILITIES = (
    "invoice.line.create",
    "invoice.line.update",
    "invoice.line.delete",
    "invoice.delete",
    "journal_entry.duplicate",
    "journal_entry.delete",
)

LINE = {
    "name": "Adjustment",
    "product_id": None,
    "account_id": 31,
    "quantity": "1",
    "price_unit": "25.5",
    "discount": "0",
    "tax_ids": [8],
}

PARAMETERS = {
    "invoice.line.create": {"move_id": 101, "line": LINE},
    "invoice.line.update": {
        "move_id": 101,
        "line_id": 201,
        "changes": {"quantity": "2", "price_unit": "30"},
    },
    "invoice.line.delete": {"move_id": 101, "line_id": 201},
    "invoice.delete": {"move_id": 101},
    "journal_entry.duplicate": {"move_id": 102},
    "journal_entry.delete": {"move_id": 102},
}


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


def _request(parameters: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "request_id": "5f377090-1157-4117-9845-2d2bbe787a67",
        "context": {
            "database": "v4-dev",
            "company_id": 7,
            "user_login": "v4-agent",
            "language": "en_US",
            "timezone": "Asia/Shanghai",
        },
        "parameters": deepcopy(parameters),
    }


@pytest.mark.parametrize("capability_id", CAPABILITIES)
def test_public_and_runtime_contracts_agree(capability_id: str) -> None:
    _, _, parameters = public.validate_core_write_request(
        capability_id, _request(PARAMETERS[capability_id])
    )

    assert runtime._valid_parameters(capability_id, parameters, 7)
    assert runtime._deterministic_key(capability_id, parameters, 7) == (
        public._expected_idempotency_key(capability_id, parameters, 7)
    )
    assert cli._CAPABILITY_MODELS[capability_id] == (
        "account.move.line"
        if capability_id.startswith("invoice.line.")
        else "account.move"
    )


def test_invoice_line_update_contract_rejects_empty_or_half_deferred_changes() -> None:
    for changes in ({}, {"deferred_start_date": "2026-09-01"}):
        request = _request(
            {"move_id": 101, "line_id": 201, "changes": changes}
        )
        with pytest.raises(public.CoreWriteError) as caught:
            public.validate_core_write_request("invoice.line.update", request)
        assert caught.value.code == "invalid_request"


class Records(list[Any]):
    @property
    def ids(self) -> list[int]:
        return [record.id for record in self]

    def filtered(self, predicate: Any) -> Records:
        return Records(record for record in self if predicate(record))

    def __getattr__(self, name: str) -> Any:
        if len(self) == 1:
            return getattr(self[0], name)
        raise AttributeError(name)


class Line:
    def __init__(self, line_id: int, owner: Records) -> None:
        self.id = line_id
        self.owner = owner
        self.display_type = "product"
        self.name = LINE["name"]
        self.product_id = SimpleNamespace(id=False)
        self.account_id = SimpleNamespace(id=LINE["account_id"])
        self.quantity = Decimal(LINE["quantity"])
        self.price_unit = Decimal(LINE["price_unit"])
        self.discount = Decimal(LINE["discount"])
        self.tax_ids = SimpleNamespace(ids=list(LINE["tax_ids"]))
        self.analytic_distribution = False
        self.deferred_start_date = False
        self.deferred_end_date = False
        self._fields: dict[str, Any] = {}

    def write(self, values: dict[str, Any]) -> None:
        for field_name, value in values.items():
            if field_name == "tax_ids":
                self.tax_ids = SimpleNamespace(ids=list(value[0][2]))
            elif field_name == "product_id":
                self.product_id = SimpleNamespace(id=value)
            else:
                setattr(self, field_name, value)

    def unlink(self) -> None:
        self.owner.remove(self)


class Invoice:
    def __init__(self, lines: Records | None = None) -> None:
        self.id = 101
        self.state = "draft"
        self.posted_before = False
        self.invoice_line_ids = lines or Records()
        self.last_write: dict[str, Any] | None = None
        self.deleted = False

    def write(self, values: dict[str, Any]) -> None:
        self.last_write = values
        command = values["invoice_line_ids"][0]
        line = Line(201 + len(self.invoice_line_ids), self.invoice_line_ids)
        for field_name, value in command[2].items():
            if field_name != "display_type":
                line.write({field_name: value})
        self.invoice_line_ids.append(line)

    def unlink(self) -> None:
        self.deleted = True


def test_invoice_line_create_uses_native_command_and_target_state_replay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    move = Invoice()
    monkeypatch.setattr(runtime, "_lifecycle_move", lambda *_args: move)
    monkeypatch.setattr(runtime, "_validate_invoice_line_references", lambda *_: None)
    monkeypatch.setattr(
        runtime,
        "_move_result",
        lambda selected, _company, source_id=None: {
            "id": selected.id,
            "source_id": source_id,
        },
    )

    result, replay = runtime._create_invoice_line(
        object(), deepcopy(PARAMETERS["invoice.line.create"]), 7, Failure
    )
    assert replay is False
    assert result == {"id": 101, "source_id": 201}
    assert move.last_write is not None
    assert move.last_write["invoice_line_ids"][0][2]["display_type"] == "product"

    result, replay = runtime._create_invoice_line(
        object(), deepcopy(PARAMETERS["invoice.line.create"]), 7, Failure
    )
    assert replay is True
    assert result == {"id": 101, "source_id": 201}
    assert len(move.invoice_line_ids) == 1


def test_invoice_line_update_and_delete_are_bound_to_the_draft_business_line(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lines = Records()
    line = Line(201, lines)
    lines.append(line)
    move = Invoice(lines)
    monkeypatch.setattr(runtime, "_lifecycle_move", lambda *_args: move)
    monkeypatch.setattr(runtime, "_search_one", lambda *_args, **_kwargs: line)
    monkeypatch.setattr(runtime, "_validate_invoice_line_references", lambda *_: None)
    monkeypatch.setattr(
        runtime,
        "_move_result",
        lambda selected, _company, source_id=None: {
            "id": selected.id,
            "source_id": source_id,
        },
    )

    result, replay = runtime._update_invoice_line(
        object(), deepcopy(PARAMETERS["invoice.line.update"]), 7, Failure
    )
    assert (result, replay) == ({"id": 101, "source_id": 201}, False)
    assert line.quantity == Decimal(2)
    assert line.price_unit == Decimal(30)

    result, replay = runtime._update_invoice_line(
        object(), deepcopy(PARAMETERS["invoice.line.update"]), 7, Failure
    )
    assert (result, replay) == ({"id": 101, "source_id": 201}, True)

    monkeypatch.setattr(
        runtime,
        "_scoped",
        lambda *_args: SimpleNamespace(search_count=lambda *_args, **_kwargs: 0),
    )
    result, replay = runtime._delete_invoice_line(
        object(), deepcopy(PARAMETERS["invoice.line.delete"]), 7, Failure
    )
    assert (result, replay) == ({"id": 101, "source_id": 201}, False)
    assert lines == []


class Entry:
    def __init__(self, entry_id: int) -> None:
        self.id = entry_id
        self.state = "posted"
        self.posted_before = entry_id == 102
        self.move_type = "entry"
        self.company_id = SimpleNamespace(id=7)
        self.journal_id = SimpleNamespace(type="general")
        self.invoice_origin = False
        self._fields: dict[str, Any] = {}
        self.deleted = False
        self.copy_record: Entry | None = None

    def write(self, values: dict[str, Any]) -> None:
        self.invoice_origin = values["invoice_origin"]

    def copy(self, default: dict[str, Any]) -> Entry:
        duplicate = Entry(202)
        duplicate.state = "draft"
        duplicate.posted_before = False
        duplicate.invoice_origin = default["invoice_origin"]
        self.copy_record = duplicate
        return duplicate

    def unlink(self) -> None:
        self.deleted = True


class MoveModel:
    def __init__(self) -> None:
        self.candidates = Records()

    def search(self, *_args: Any, **_kwargs: Any) -> Records:
        return self.candidates

    def search_count(self, *_args: Any, **_kwargs: Any) -> int:
        return 0


@pytest.mark.parametrize(
    "field_name",
    [
        "origin_payment_id",
        "statement_line_id",
        "tax_cash_basis_origin_move_id",
        "reversed_entry_id",
        "reversal_move_ids",
        "auto_post_origin_id",
        "asset_id",
        "asset_value_change",
        "deferred_original_move_ids",
        "transfer_model_id",
    ],
)
def test_generated_journal_entry_sources_match_odoo_19_fields(
    field_name: str,
) -> None:
    move = SimpleNamespace(_fields={field_name: object()})
    setattr(move, field_name, True)

    assert runtime._generated_entry(move) is True


def test_journal_entry_duplicate_uses_native_copy_and_marker_replay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = Entry(102)
    model = MoveModel()
    monkeypatch.setattr(runtime, "_lifecycle_move", lambda *_args: source)
    monkeypatch.setattr(runtime, "_scoped", lambda *_args: model)
    monkeypatch.setattr(
        runtime,
        "_move_result",
        lambda selected, _company, source_id=None: {
            "id": selected.id,
            "source_id": source_id,
        },
    )

    result, replay = runtime._duplicate_journal_entry(
        object(), {"move_id": 102}, 7, "journal-copy-key", Failure
    )
    assert (result, replay) == ({"id": 202, "source_id": 102}, False)
    assert source.copy_record is not None
    assert "ODACV4K:" in source.copy_record.invoice_origin
    assert "ODACV4:" in source.copy_record.invoice_origin

    model.candidates = Records([source.copy_record])
    result, replay = runtime._duplicate_journal_entry(
        object(), {"move_id": 102}, 7, "journal-copy-key", Failure
    )
    assert (result, replay) == ({"id": 202, "source_id": 102}, True)


@pytest.mark.parametrize("capability_id", ["invoice.delete", "journal_entry.delete"])
def test_whole_document_delete_requires_a_never_posted_draft(
    monkeypatch: pytest.MonkeyPatch, capability_id: str
) -> None:
    move = Entry(102) if capability_id.startswith("journal") else Invoice()
    move.state = "draft"
    move.posted_before = False
    monkeypatch.setattr(runtime, "_lifecycle_move", lambda *_args: move)
    monkeypatch.setattr(
        runtime,
        "_move_result",
        lambda selected, _company: {
            "model": "account.move",
            "id": selected.id,
            "name": "DRAFT",
            "state": selected.state,
            "company_id": 7,
            "move_type": getattr(selected, "move_type", "out_invoice"),
            "source_id": None,
            "line_ids": [],
            "partial_reconcile_ids": [],
            "full_reconcile_id": None,
            "reconciled": False,
        },
    )
    monkeypatch.setattr(
        runtime,
        "_scoped",
        lambda *_args: SimpleNamespace(search_count=lambda *_args, **_kwargs: 0),
    )

    result, replay = runtime._delete_draft_move(
        object(), capability_id, {"move_id": move.id}, 7, Failure
    )
    assert replay is False
    assert result["state"] == "deleted"
    assert move.deleted is True

    move.deleted = False
    move.posted_before = True
    with pytest.raises(Failure) as caught:
        runtime._delete_draft_move(
            object(), capability_id, {"move_id": move.id}, 7, Failure
        )
    assert caught.value.code == "state_conflict"
    assert move.deleted is False
