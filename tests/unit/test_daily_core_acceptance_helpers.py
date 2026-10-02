"""Local checks for the bounded native smoke's assertion helpers."""

import importlib
import uuid
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def smoke(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "integration"))
    return importlib.import_module("test_daily_core_acceptance_live")


class Rows(list):
    company_id = SimpleNamespace(currency_id=SimpleNamespace(id=6))


@pytest.mark.parametrize("fault", [None, "group_amount", "total_amount", "group_count", "total_count", "empty_groups", "empty_rows"])
def test_summary_checks_native_amounts_and_counts(smoke, fault):
    rows = Rows([{"journal": 7, "amount": "1.20"}, {"journal": 7, "amount": "2.30"}])
    data = {"company_id": 1, "company_currency": {"id": 6}, "groups": [
        {"group": {"id": 7, "value": None}, "row_count": 2, "debit": "3.50"}],
        "totals": {"row_count": 2, "debit": "3.50"}}
    if fault in {"group_amount", "group_count"}:
        data["groups"][0]["debit" if fault == "group_amount" else "row_count"] = "3.51" if fault == "group_amount" else 1
    elif fault in {"total_amount", "total_count"}:
        data["totals"]["debit" if fault == "total_amount" else "row_count"] = "3.51" if fault == "total_amount" else 1
    elif fault == "empty_groups":
        data["groups"] = []
    elif fault == "empty_rows":
        rows.clear()
    arguments = (data, rows, lambda row: row["journal"], {"debit": "amount"}, Decimal("0.01"))
    if fault is None:
        smoke._assert_summary(*arguments)
    else:
        with pytest.raises(AssertionError):
            smoke._assert_summary(*arguments)


def test_keys_use_production_normalization_and_preserve_creation_intent(smoke):
    case = smoke._Case.__new__(smoke._Case)
    case.alias, case.run_id, case.counter = "sandbox-a", uuid.uuid4(), 0
    assert case.key("invoice.post", {"move_id": 17}) == "invoice.post:17"
    params = {"move_id": 17, "line_id": 19, "changes": {"price_unit": "12"}}
    key = case.key("invoice.line.update", params)
    assert case.key("invoice.line.update", dict(reversed(list(params.items())))) == key
    assert case.key("invoice.line.update", {**params, "changes": {"price_unit": "13"}}) != key
    create = {"journal_id": 3, "date": "2026-10-02", "lines": [
        {"name": "debit", "account_id": 11, "partner_id": None, "debit": "10", "credit": "0"},
        {"name": "credit", "account_id": 12, "partner_id": None, "debit": "0", "credit": "10"}]}
    assert case.key("journal_entry.create", create, "owned") == case.key("journal_entry.create", create, "owned")
    assert case.key("journal_entry.create", create) != case.key("journal_entry.create", create)


@pytest.mark.parametrize("fault", [None, "first_replay", "second_not_replay", "different_result"])
def test_write_rejects_dishonest_replay(smoke, fault):
    case = smoke._Case.__new__(smoke._Case)
    case.key = lambda *args: "stable-key"
    result = {"id": 17}
    first = {"data": {"idempotent_replay": fault == "first_replay", "result": deepcopy(result)}}
    second = {"data": {"idempotent_replay": fault != "second_not_replay", "result": {"id": 18} if fault == "different_result" else deepcopy(result)}}
    calls, replies = [], iter((first, second))

    def call(*args, **kwargs):
        calls.append(kwargs["key"])
        return next(replies)

    case._call = call
    if fault is None:
        assert case.write("invoice.post", {"move_id": 17}, replay=True) == result
        assert calls == ["stable-key", "stable-key"]
    else:
        with pytest.raises(AssertionError):
            case.write("invoice.post", {"move_id": 17}, replay=True)


@pytest.mark.parametrize("value,kind,expected", [(None, "monetary", None), (False, "float", None), ("", "date", None), (0, "monetary", Decimal(0)), ("12.30", "monetary", Decimal("12.30")), ("2026-10-02", "date", "2026-10-02"), ("USD", "string", "USD")])
def test_report_values_keep_native_numeric_and_text_types(smoke, value, kind, expected):
    assert smoke._report_value(value, kind) == expected
