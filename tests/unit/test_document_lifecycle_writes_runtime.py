from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace
from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge import core_writes_runtime as runtime
from odoo_accounting_cli_v4.capabilities import core_writes as public

_PARAMETERS: dict[str, dict[str, Any]] = {
    "invoice.update": {"move_id": 101, "changes": {"reference": "PO-101"}},
    "invoice.lines.replace": {
        "move_id": 102,
        "lines": [
            {
                "name": "Replacement invoice line",
                "product_id": None,
                "account_id": 31,
                "quantity": "2.00",
                "price_unit": "30.50",
                "discount": "5",
                "tax_ids": [8, 9],
            }
        ],
    },
    "invoice.cancel": {"move_id": 103},
    "invoice.reset_to_draft": {"move_id": 104},
    "journal_entry.update": {
        "move_id": 105,
        "changes": {"reference": None},
    },
    "journal_entry.lines.replace": {
        "move_id": 106,
        "lines": [
            {
                "name": "Debit",
                "account_id": 31,
                "partner_id": None,
                "debit": "100.00",
                "credit": "0",
            },
            {
                "name": "Credit",
                "account_id": 32,
                "partner_id": 21,
                "debit": "0",
                "credit": "100.00",
            },
        ],
    },
    "journal_entry.cancel": {"move_id": 107},
    "journal_entry.reset_to_draft": {"move_id": 108},
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


@pytest.mark.parametrize("capability_id", tuple(_PARAMETERS))
def test_runtime_validation_and_deterministic_keys_match_the_public_contract(
    capability_id: str,
) -> None:
    parameters = deepcopy(_PARAMETERS[capability_id])
    _, _, normalized = public.validate_core_write_request(
        capability_id, _request(parameters)
    )

    assert runtime._valid_parameters(capability_id, normalized)
    assert runtime._deterministic_key(capability_id, normalized, 7) == (
        public._expected_idempotency_key(capability_id, normalized, 7)
    )


class _CreateModel:
    def __init__(self) -> None:
        self.values: dict[str, Any] | None = None
        self.record = SimpleNamespace(id=901)

    def create(self, values: dict[str, Any]) -> Any:
        self.values = values
        return self.record


@pytest.mark.parametrize(
    ("capability_id", "parameters", "invoke"),
    [
        (
            "customer_invoice.create",
            {
                "partner_id": 21,
                "journal_id": 4,
                "invoice_date": "2026-08-26",
                "currency_id": 6,
                "lines": [
                    {
                        "name": "Invoice line",
                        "account_id": 31,
                        "quantity": "1",
                        "price_unit": "25",
                        "tax_ids": [],
                    }
                ],
            },
            "document",
        ),
        (
            "journal_entry.create",
            {
                "journal_id": 5,
                "date": "2026-08-26",
                "lines": _PARAMETERS["journal_entry.lines.replace"]["lines"],
            },
            "entry",
        ),
    ],
)
def test_new_move_creates_use_origin_markers_without_occupying_business_ref(
    monkeypatch: pytest.MonkeyPatch,
    capability_id: str,
    parameters: dict[str, Any],
    invoke: str,
) -> None:
    model = _CreateModel()
    key = f"marker-migration-{capability_id}"
    marker = "ODACV4:parameter-fingerprint"
    monkeypatch.setattr(runtime, "_existing_move_for_key", lambda *_args: None)
    monkeypatch.setattr(runtime, "_ensure_ids", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        runtime,
        "_search_one",
        lambda *_args, **_kwargs: SimpleNamespace(currency_id=SimpleNamespace(id=6)),
    )
    monkeypatch.setattr(runtime, "_scoped", lambda *_args: model)
    monkeypatch.setattr(
        runtime,
        "_move_result",
        lambda move, company_id: {"id": move.id, "company_id": company_id},
    )

    if invoke == "document":
        result, replay = runtime._create_document(
            object(), capability_id, parameters, 7, key, marker, Failure
        )
    else:
        result, replay = runtime._create_entry(
            object(), parameters, 7, key, marker, Failure
        )

    assert replay is False
    assert result == {"id": 901, "company_id": 7}
    assert model.values is not None
    assert "ref" not in model.values
    assert model.values["invoice_origin"] == (
        f"{runtime._idempotency_key_marker(capability_id, 7, key)};{marker}"
    )


class _Move:
    def __init__(self, state: str) -> None:
        self.state = state
        self.values: dict[str, Any] | None = None
        self.native_calls: list[str] = []

    def write(self, values: dict[str, Any]) -> None:
        self.values = values

    def button_cancel(self) -> None:
        self.native_calls.append("button_cancel")
        self.state = "cancel"

    def button_draft(self) -> None:
        self.native_calls.append("button_draft")
        self.state = "draft"


class _Records(list[Any]):
    @property
    def ids(self) -> list[int]:
        return [record.id for record in self]

    def filtered(self, predicate: Any) -> _Records:
        return _Records(record for record in self if predicate(record))


class _MoveSearchModel:
    def __init__(self, new: _Records, legacy: _Records) -> None:
        self.new = new
        self.legacy = legacy
        self.records = {record.id: record for record in new + legacy}

    def search(self, domain: list[Any], **_kwargs: Any) -> _Records:
        fields = {condition[0] for condition in domain if isinstance(condition, tuple)}
        return self.new if "invoice_origin" in fields else self.legacy

    def browse(self, record_id: int) -> Any:
        return self.records[record_id]


@pytest.mark.parametrize("legacy", [False, True])
def test_create_replay_accepts_new_origin_markers_and_legacy_ref_records(
    monkeypatch: pytest.MonkeyPatch, legacy: bool
) -> None:
    capability_id = "customer_invoice.create"
    key = "compatible-create-key"
    marker = "ODACV4:parameter-fingerprint"
    key_marker = runtime._idempotency_key_marker(capability_id, 7, key)
    record = SimpleNamespace(
        id=901,
        invoice_origin=marker if legacy else f"{key_marker};{marker}",
    )
    model = _MoveSearchModel(
        _Records() if legacy else _Records([record]),
        _Records([record]) if legacy else _Records(),
    )
    monkeypatch.setattr(runtime, "_scoped", lambda *_args: model)

    assert (
        runtime._existing_move_for_key(
            object(), capability_id, 7, key, "out_invoice", marker, Failure
        )
        is record
    )

    with pytest.raises(Failure) as caught:
        runtime._existing_move_for_key(
            object(),
            capability_id,
            7,
            key,
            "out_invoice",
            "ODACV4:different-parameters",
            Failure,
        )
    assert caught.value.code == "idempotency_conflict"


def test_update_writes_only_a_draft_and_replays_an_equal_later_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    move = _Move("draft")
    requested = {"reference": "PO-101"}
    current_values = iter([{"reference": None}, requested])
    monkeypatch.setattr(runtime, "_lifecycle_move", lambda *_args: move)
    monkeypatch.setattr(
        runtime, "_validate_invoice_update_references", lambda *_args: None
    )
    monkeypatch.setattr(
        runtime, "_current_invoice_changes", lambda *_args: next(current_values)
    )
    monkeypatch.setattr(runtime, "_move_result", lambda *_args: {"id": 101})

    result, replay = runtime._update_move(
        object(),
        "invoice.update",
        {"move_id": 101, "changes": requested},
        7,
        Failure,
    )

    assert (result, replay) == ({"id": 101}, False)
    assert move.values == {"ref": "PO-101"}

    posted = _Move("posted")
    monkeypatch.setattr(runtime, "_lifecycle_move", lambda *_args: posted)
    monkeypatch.setattr(runtime, "_current_invoice_changes", lambda *_args: requested)
    assert runtime._update_move(
        object(),
        "invoice.update",
        {"move_id": 101, "changes": requested},
        7,
        Failure,
    ) == ({"id": 101}, True)
    assert posted.values is None


def test_invoice_line_replace_is_atomic_and_rejects_external_source_links(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    move = _Move("draft")
    parameters = deepcopy(_PARAMETERS["invoice.lines.replace"])
    expected = runtime._normalized_invoice_replacement_lines(parameters["lines"])
    current_values = iter([[], expected])
    monkeypatch.setattr(runtime, "_lifecycle_move", lambda *_args: move)
    monkeypatch.setattr(
        runtime, "_validate_invoice_line_references", lambda *_args: None
    )
    monkeypatch.setattr(
        runtime, "_current_invoice_lines", lambda *_args: next(current_values)
    )
    monkeypatch.setattr(runtime, "_has_external_invoice_line_source", lambda *_: False)
    monkeypatch.setattr(runtime, "_move_result", lambda *_args: {"id": 102})

    result, replay = runtime._replace_move_lines(
        object(), "invoice.lines.replace", parameters, 7, Failure
    )

    assert (result, replay) == ({"id": 102}, False)
    assert move.values is not None
    commands = move.values["invoice_line_ids"]
    assert commands[0] == (5, 0, 0)
    assert commands[1][0:2] == (0, 0)
    assert commands[1][2]["sequence"] == 10

    linked = _Move("draft")
    monkeypatch.setattr(runtime, "_lifecycle_move", lambda *_args: linked)
    monkeypatch.setattr(runtime, "_current_invoice_lines", lambda *_args: [])
    monkeypatch.setattr(runtime, "_has_external_invoice_line_source", lambda *_: True)
    with pytest.raises(Failure) as caught:
        runtime._replace_move_lines(
            object(), "invoice.lines.replace", parameters, 7, Failure
        )
    assert caught.value.code == "business_rule_error"
    assert linked.values is None


@pytest.mark.parametrize(
    ("capability_id", "initial", "target", "native_method"),
    [
        ("invoice.cancel", "posted", "cancel", "button_cancel"),
        ("invoice.reset_to_draft", "posted", "draft", "button_draft"),
        ("journal_entry.cancel", "draft", "cancel", "button_cancel"),
        ("journal_entry.reset_to_draft", "cancel", "draft", "button_draft"),
    ],
)
def test_transitions_use_native_methods_and_target_state_replay(
    monkeypatch: pytest.MonkeyPatch,
    capability_id: str,
    initial: str,
    target: str,
    native_method: str,
) -> None:
    move = _Move(initial)
    monkeypatch.setattr(runtime, "_lifecycle_move", lambda *_args: move)
    monkeypatch.setattr(
        runtime,
        "_move_result",
        lambda selected, _company: {"state": selected.state},
    )

    result, replay = runtime._transition_move(
        object(), capability_id, {"move_id": 103}, 7, Failure
    )
    assert (result, replay) == ({"state": target}, False)
    assert move.native_calls == [native_method]

    move.native_calls.clear()
    result, replay = runtime._transition_move(
        object(), capability_id, {"move_id": 103}, 7, Failure
    )
    assert (result, replay) == ({"state": target}, True)
    assert move.native_calls == []
