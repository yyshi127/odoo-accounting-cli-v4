from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge import core_writes_runtime as runtime

CAPABILITIES = {
    "payment_term.create",
    "payment_term.update",
    "payment_term.lines.replace",
    "payment_term.archive",
    "payment_term.restore",
    "period.accrual.generate",
}
LINE = {
    "value": "percent",
    "value_amount": "100",
    "delay_type": "days_after",
    "nb_days": 30,
}


class Failure(Exception):
    def __init__(self, *_args: Any, **kwargs: Any) -> None:
        self.code = kwargs.get("code")


class Record:
    def __init__(self, **values: Any) -> None:
        self.__dict__.update(values)
        self.writes: list[dict[str, Any]] = []

    def write(self, values: dict[str, Any]) -> None:
        self.writes.append(values)
        for key, value in values.items():
            setattr(self, key, value)

    def invalidate_recordset(self, _fields: list[str]) -> None:
        return None


class Records(list[Record]):
    @property
    def ids(self) -> list[int]:
        return [item.id for item in self]

    def filtered(self, predicate: Any) -> Records:
        return Records(item for item in self if predicate(item))

    def __getattr__(self, name: str) -> Any:
        if len(self) != 1:
            raise AttributeError(name)
        return getattr(self[0], name)

    def __add__(self, other: Any) -> Records:
        return Records([*self, *other])

    def write(self, values: dict[str, Any]) -> None:
        for record in self:
            record.write(values)


def _term(*, active: bool = True) -> Record:
    return Record(
        id=21,
        name="Net 30",
        active=active,
        company_id=SimpleNamespace(id=7),
        line_ids=Records(
            [
                Record(
                    id=31,
                    value="fixed",
                    value_amount=10,
                    delay_type="days_after",
                    nb_days=0,
                    days_next_month=0,
                )
            ]
        ),
    )


def test_closed_batch_metadata_is_manager_only_and_has_no_stock_models() -> None:
    assert CAPABILITIES <= runtime.CAPABILITIES
    assert {runtime._GROUPS[item] for item in CAPABILITIES} == {
        "account.group_account_manager"
    }
    assert all(
        not any(model.startswith("stock.") for model in runtime._MODELS[item])
        for item in CAPABILITIES
    )
    assert "account.accrued.orders.wizard" in runtime._MODELS["period.accrual.generate"]


def test_payment_term_parameters_require_requested_company_and_valid_lines() -> None:
    parameters = {"name": "Net 30", "company_id": 7, "lines": [LINE]}
    assert runtime._valid_parameters("payment_term.create", parameters, 7)
    assert not runtime._valid_parameters("payment_term.create", parameters, 8)
    assert not runtime._valid_parameters(
        "payment_term.create",
        {
            **parameters,
            "lines": [{**LINE, "value_amount": "90"}],
        },
        7,
    )


def test_accrual_parameters_limit_manual_amount_to_one_order() -> None:
    parameters = {
        "source_model": "purchase.order",
        "order_ids": [41],
        "date": "2026-08-31",
        "reversal_date": "2026-09-01",
        "journal_id": 11,
        "accrual_account_id": 12,
        "amount": "25",
    }
    assert runtime._valid_parameters("period.accrual.generate", parameters, 7)
    assert not runtime._valid_parameters(
        "period.accrual.generate", {**parameters, "order_ids": [41, 42]}, 7
    )


def test_payment_term_create_uses_company_and_native_line_commands(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created: dict[str, Any] = {}
    term = _term()
    model = SimpleNamespace(
        search=lambda *_args, **_kwargs: Records(),
        create=lambda values: (created.update(values), term)[1],
    )
    monkeypatch.setattr(runtime, "_scoped", lambda *_args: model)

    result, replay = runtime._create_payment_term(
        object(),
        {"name": "Net 30", "company_id": 7, "lines": [LINE]},
        7,
        Failure,
    )

    assert not replay
    assert created["company_id"] == 7
    assert created["line_ids"] == [(0, 0, LINE | {"value_amount": 100.0})]
    assert result["model"] == "account.payment.term"
    assert result["line_ids"] == [31]


def test_payment_term_create_replays_exact_company_name_and_lines(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    term = _term()
    term.line_ids = Records(
        [
            Record(
                id=31,
                value="percent",
                value_amount=100,
                delay_type="days_after",
                nb_days=30,
                days_next_month="10",
            )
        ]
    )
    model = SimpleNamespace(search=lambda *_args, **_kwargs: Records([term]))
    monkeypatch.setattr(runtime, "_scoped", lambda *_args: model)

    result, replay = runtime._create_payment_term(
        object(),
        {"name": "Net 30", "company_id": 7, "lines": [LINE]},
        7,
        Failure,
    )

    assert replay
    assert result["id"] == 21


def test_payment_term_replace_uses_clear_then_create(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    term = _term()
    monkeypatch.setattr(runtime, "_payment_term", lambda *_args: term)

    result, replay = runtime._replace_payment_term_lines(
        object(), {"payment_term_id": 21, "lines": [LINE]}, 7, Failure
    )

    assert not replay
    assert term.writes == [
        {"line_ids": [(5, 0, 0), (0, 0, LINE | {"value_amount": 100.0})]}
    ]
    assert result["id"] == 21


def test_payment_term_default_days_next_month_replays_odoo_char_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    term = _term()
    term.line_ids = Records(
        [
            Record(
                id=31,
                value="percent",
                value_amount=100,
                delay_type="days_after",
                nb_days=30,
                days_next_month="10",
            )
        ]
    )
    monkeypatch.setattr(runtime, "_payment_term", lambda *_args: term)

    _, replay = runtime._replace_payment_term_lines(
        object(), {"payment_term_id": 21, "lines": [LINE]}, 7, Failure
    )

    assert replay
    assert term.writes == []


def test_payment_term_explicit_days_next_month_is_written_as_odoo_char() -> None:
    line = LINE | {"days_next_month": 15}
    assert runtime._payment_term_line_commands([line]) == [
        (5, 0, 0),
        (0, 0, line | {"value_amount": 100.0, "days_next_month": "15"}),
    ]


def test_payment_term_update_does_not_clear_omitted_note(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    term = _term()
    term.sequence = 1
    term.note = "Keep me"
    monkeypatch.setattr(runtime, "_payment_term", lambda *_args: term)

    runtime._update_payment_term(
        object(), {"payment_term_id": 21, "sequence": 2}, 7, Failure
    )

    assert term.writes == [{"sequence": 2}]
    assert term.note == "Keep me"


def test_payment_term_archive_and_restore_are_replay_safe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    term = _term(active=True)
    monkeypatch.setattr(runtime, "_payment_term", lambda *_args: term)
    parameters = {"payment_term_id": 21}

    _, replay = runtime._transition_payment_term(
        object(), "payment_term.archive", parameters, 7, Failure
    )
    assert not replay
    _, replay = runtime._transition_payment_term(
        object(), "payment_term.archive", parameters, 7, Failure
    )
    assert replay
    _, replay = runtime._transition_payment_term(
        object(), "payment_term.restore", parameters, 7, Failure
    )
    assert not replay


def test_deterministic_keys_cover_payment_term_content_and_lifecycle() -> None:
    update = runtime._deterministic_key(
        "payment_term.update", {"payment_term_id": 21, "note": "Changed"}, 7
    )
    replace = runtime._deterministic_key(
        "payment_term.lines.replace", {"payment_term_id": 21, "lines": [LINE]}, 7
    )
    assert update and update.startswith("payment_term.update:21:")
    assert replace and replace.startswith("payment_term.lines.replace:21:")
    assert (
        runtime._deterministic_key("payment_term.archive", {"payment_term_id": 21}, 7)
        == "payment_term.archive:21"
    )
    assert runtime._deterministic_key("period.accrual.generate", {}, 7) is None


def test_accrual_uses_native_wizard_and_verifies_posted_move_pair(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    orders = Records([Record(id=41)])
    primary = Record(
        id=51,
        date="2026-08-31",
        name="ACCR/1",
        state="posted",
        move_type="entry",
        line_ids=Records([Record(id=61, reconciled=False)]),
        invoice_origin=False,
    )
    reversal = Record(
        id=52,
        date="2026-09-01",
        name="ACCR/2",
        state="posted",
        move_type="entry",
        line_ids=Records([Record(id=62, reconciled=False)]),
        invoice_origin=False,
    )
    wizard_values: dict[str, Any] = {}
    search_domains: dict[str, list[Any]] = {}
    wizard = SimpleNamespace(
        create_entries=lambda: {"domain": [("id", "in", [primary.id, reversal.id])]}
    )

    def ensure_ids(_env: Any, model: str, *_args: Any, **_kwargs: Any) -> Records:
        return orders if model == "purchase.order" else Records([primary, reversal])

    class WizardModel:
        def with_context(self, **context: Any) -> WizardModel:
            assert context == {
                "active_model": "purchase.order",
                "active_ids": [41],
            }
            return self

        def create(self, values: dict[str, Any]) -> Any:
            wizard_values.update(values)
            return wizard

    monkeypatch.setattr(runtime, "_ensure_ids", ensure_ids)
    monkeypatch.setattr(runtime, "_generated_pair_for_key", lambda *_args: None)
    monkeypatch.setattr(
        runtime,
        "_search_one",
        lambda _env, model, domain, *_args, **_kwargs: (
            search_domains.update({model: domain}),
            Record(id=11 if model == "account.journal" else 12),
        )[1],
    )
    monkeypatch.setattr(runtime, "_scoped", lambda *_args: WizardModel())
    parameters = {
        "source_model": "purchase.order",
        "order_ids": [41],
        "date": "2026-08-31",
        "reversal_date": "2026-09-01",
        "journal_id": 11,
        "accrual_account_id": 12,
        "amount": "25",
    }

    result, replay = runtime._generate_period_accrual(
        object(), parameters, 7, "period.accrual.generate:test-key", Failure
    )

    assert not replay
    assert wizard_values == {
        "company_id": 7,
        "journal_id": 11,
        "date": "2026-08-31",
        "reversal_date": "2026-09-01",
        "account_id": 12,
        "amount": 25.0,
    }
    assert ("account_type", "=", "liability_current") in search_domains[
        "account.account"
    ]
    assert result["id"] == 51
    assert result["source_id"] == 52
    assert result["state"] == "posted"
    assert result["line_ids"] == [61]


def test_accrual_replays_verified_marked_pair(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    primary = Record(
        id=51,
        date="2026-08-31",
        name="ACCR/1",
        state="posted",
        move_type="entry",
        line_ids=Records([Record(id=61, reconciled=False)]),
    )
    reversal = Record(
        id=52,
        date="2026-09-01",
        state="posted",
    )
    monkeypatch.setattr(
        runtime,
        "_generated_pair_for_key",
        lambda *_args: (Records([primary]), Records([reversal])),
    )
    parameters = {
        "source_model": "purchase.order",
        "order_ids": [41],
        "date": "2026-08-31",
        "reversal_date": "2026-09-01",
        "journal_id": 11,
        "accrual_account_id": 12,
    }

    result, replay = runtime._generate_period_accrual(
        object(), parameters, 7, "period.accrual.generate:test-key", Failure
    )

    assert replay
    assert result["id"] == 51
    assert result["source_id"] == 52
