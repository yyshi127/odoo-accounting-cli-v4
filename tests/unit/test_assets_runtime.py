from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge import assets_runtime as assets


class Failure(RuntimeError):
    def __init__(self, code: str, message: str, *, exit_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


class Records(list):
    @property
    def ids(self) -> list[int]:
        return [record.id for record in self]


def _record(record_id: int, **values: Any) -> SimpleNamespace:
    return SimpleNamespace(id=record_id, **values)


def _related_id(value: Any) -> Any:
    return getattr(value, "id", value)


class Model:
    def __init__(
        self,
        rows: list[Any] | None = None,
        *,
        fields: set[str] | None = None,
        access: bool = True,
    ) -> None:
        self.rows = Records(rows or [])
        self._fields = {name: object() for name in (fields or set())}
        self.access = access
        self.calls: list[tuple[Any, ...]] = []

    def with_context(self, **context: Any) -> Model:
        self.calls.append(("with_context", context))
        return self

    def has_access(self, operation: str) -> bool:
        self.calls.append(("has_access", operation))
        return self.access

    def _matches(self, row: Any, domain: list[Any]) -> bool:
        for term in domain:
            if not isinstance(term, tuple):
                continue
            field, operator, expected = term
            actual = _related_id(getattr(row, field))
            if operator == "=" and actual != expected:
                return False
            if operator == "<" and actual >= expected:
                return False
            if operator == "in" and actual not in expected:
                return False
            if operator == "ilike" and expected.casefold() not in actual.casefold():
                return False
        return True

    def search_count(self, domain: list[Any], *, limit: int) -> int:
        self.calls.append(("search_count", domain, limit))
        return min(limit, sum(self._matches(row, domain) for row in self.rows))

    def search(
        self,
        domain: list[Any],
        *,
        order: str | None = None,
        limit: int,
    ) -> Records:
        self.calls.append(("search", domain, order, limit))
        rows = [row for row in self.rows if self._matches(row, domain)]
        if order == "id desc":
            rows.sort(key=lambda row: row.id, reverse=True)
        return Records(rows[:limit])


class User:
    def __init__(self, allowed: bool = True) -> None:
        self.allowed = allowed

    def has_group(self, xml_id: str) -> bool:
        assert xml_id == "account.group_account_readonly"
        return self.allowed


class Registry:
    def __init__(self, models: dict[str, Model]) -> None:
        self.models = models

    def get(self, name: str) -> Model | None:
        return self.models.get(name)


class Env:
    def __init__(self, models: dict[str, Model]) -> None:
        self.uid = 5
        self.user = User()
        self.models = models
        self.registry = Registry(models)

    def __getitem__(self, name: str) -> Model:
        return self.models[name]


def _fixture() -> tuple[Env, dict[str, Any]]:
    company = _record(7, name="Demo Company")
    other_company = _record(8, name="Other Company")
    currency = _record(6, name="CNY")
    asset_account = _record(
        78, code="1601", name="Fixed Assets", company_ids=Records([company])
    )
    depreciation_account = _record(
        80, code="160301", name="Accumulated", company_ids=Records([company])
    )
    expense_account = _record(
        146, code="6602", name="Expense", company_ids=Records([company])
    )
    journal = _record(11, code="MISC", name="Miscellaneous", company_id=company)
    asset = _record(
        31,
        name="Office Equipment",
        state="open",
        active=True,
        company_id=company,
        currency_id=currency,
        acquisition_date=date(2025, 1, 1),
        prorata_date=date(2025, 1, 1),
        disposal_date=False,
        account_asset_id=asset_account,
        account_depreciation_id=depreciation_account,
        account_depreciation_expense_id=expense_account,
        journal_id=journal,
        original_value=120,
        salvage_value=0,
        total_depreciable_value=120,
        book_value=60,
        value_residual=60,
        method="linear",
        method_number=2,
        method_period="12",
        method_progress_factor=0.3,
        prorata_computation_type="none",
        depreciation_move_ids=Records(),
    )
    lines = Records([_record(101), _record(102)])
    move = _record(
        91,
        name="MISC/2025/0001",
        date=date(2025, 12, 31),
        state="posted",
        auto_post="no",
        company_id=company,
        journal_id=journal,
        asset_id=asset,
        depreciation_value=60,
        asset_depreciated_value=60,
        asset_remaining_value=60,
        line_ids=lines,
    )
    asset.depreciation_move_ids = Records([move])
    asset_values = {key: value for key, value in asset.__dict__.items() if key != "id"}
    model_asset = _record(32, **{**asset_values, "name": "Template", "state": "model"})
    other_asset = _record(
        33,
        **{
            **asset_values,
            "name": "Other Asset",
            "company_id": other_company,
        },
    )
    asset_fields = set(asset.__dict__) - {"id"}
    move_fields = set(move.__dict__) - {"id"}
    models = {
        "account.asset": Model([asset, model_asset, other_asset], fields=asset_fields),
        "account.move": Model([move], fields=move_fields),
        "account.move.line": Model(lines),
        "account.account": Model(
            [asset_account, depreciation_account, expense_account],
            fields={"code", "name"},
        ),
        "account.journal": Model([journal], fields={"code", "name", "company_id"}),
        "res.company": Model([company, other_company]),
        "res.currency": Model([currency], fields={"name"}),
    }
    return Env(models), {
        "asset": asset,
        "move": move,
        "asset_account": asset_account,
    }


def _dispatch(
    env: Env, capability_id: str, parameters: dict[str, Any]
) -> dict[str, Any]:
    return assets.dispatch(
        env,
        {
            "capability_id": capability_id,
            "company_id": 7,
            "parameters": parameters,
        },
        7,
        failure_type=Failure,
    )


def test_search_is_company_scoped_excludes_models_and_orders_by_descending_id() -> None:
    env, _ = _fixture()
    page = _dispatch(
        env,
        "asset.search",
        {"query": "Office", "states": ["open"], "after": None, "limit": 2},
    )

    assert page["items"] == [
        {
            "id": 31,
            "name": "Office Equipment",
            "state": "open",
            "company_id": 7,
            "currency": {"id": 6, "code": "CNY"},
            "acquisition_date": "2025-01-01",
            "original_value": "120",
            "book_value": "60",
        }
    ]
    search_call = next(
        call for call in env.models["account.asset"].calls if call[0] == "search"
    )
    assert ("company_id", "=", 7) in search_call[1]
    assert ("state", "in", ["open"]) in search_call[1]
    assert search_call[2:] == ("id desc", 2)


def test_search_cursor_must_exist_in_the_same_filter_scope() -> None:
    env, _ = _fixture()
    page = _dispatch(
        env,
        "asset.search",
        {"query": None, "states": ["open"], "after": 999, "limit": 2},
    )
    assert page["cursor_found"] is False
    assert page["items"] == []


def test_get_returns_compact_values_accounts_method_and_dates() -> None:
    env, _ = _fixture()
    page = _dispatch(env, "asset.get", {"asset_id": 31})
    item = page["items"][0]

    assert item["accounts"] == {
        "asset": {"id": 78, "code": "1601", "name": "Fixed Assets"},
        "depreciation": {"id": 80, "code": "160301", "name": "Accumulated"},
        "expense": {"id": 146, "code": "6602", "name": "Expense"},
    }
    assert item["values"] == {
        "original": "120",
        "salvage": "0",
        "depreciable": "120",
        "book": "60",
        "residual": "60",
    }
    assert item["method"]["number"] == 2
    assert item["dates"] == {
        "acquisition": "2025-01-01",
        "prorata": "2025-01-01",
        "disposal": None,
    }


def test_schedule_returns_only_direct_company_scoped_depreciation_moves() -> None:
    env, _ = _fixture()
    page = _dispatch(env, "asset.depreciation_schedule.get", {"asset_id": 31})

    assert page["items"][0]["asset"]["id"] == 31
    assert page["items"][0]["moves"] == [
        {
            "id": 91,
            "name": "MISC/2025/0001",
            "date": "2025-12-31",
            "state": "posted",
            "auto_post": "no",
            "journal": {"id": 11, "code": "MISC", "name": "Miscellaneous"},
            "depreciation_value": "60",
            "cumulative_depreciation": "60",
            "remaining_value": "60",
            "line_ids": [101, 102],
        }
    ]


@pytest.mark.parametrize(
    "capability_id", ["asset.get", "asset.depreciation_schedule.get"]
)
def test_missing_or_other_company_asset_is_an_empty_result(capability_id: str) -> None:
    env, _ = _fixture()
    assert _dispatch(env, capability_id, {"asset_id": 33})["items"] == []
    assert _dispatch(env, capability_id, {"asset_id": 999})["items"] == []


def test_acl_denial_returns_no_records() -> None:
    env, _ = _fixture()
    env.models["account.move"].access = False

    assert _dispatch(
        env,
        "asset.search",
        {"query": None, "states": ["open"], "after": None, "limit": 2},
    ) == {
        "user_id": 5,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": False,
        "cursor_found": True,
        "items": [],
    }


def test_cross_company_related_account_fails_closed() -> None:
    env, records = _fixture()
    records["asset_account"].company_ids = Records([_record(8)])

    with pytest.raises(Failure) as caught:
        _dispatch(env, "asset.get", {"asset_id": 31})

    assert caught.value.code == "odoo_runtime_error"


def test_required_field_drift_fails_closed() -> None:
    env, _ = _fixture()
    del env.models["account.asset"]._fields["book_value"]

    with pytest.raises(Failure) as caught:
        _dispatch(env, "asset.get", {"asset_id": 31})

    assert caught.value.code == "odoo_runtime_error"


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    [
        ("asset.search", {"query": None, "states": ["open"], "after": None}),
        (
            "asset.search",
            {"query": None, "states": ["open", "open"], "after": None, "limit": 2},
        ),
        (
            "asset.search",
            {"query": None, "states": ["model"], "after": None, "limit": 2},
        ),
        (
            "asset.search",
            {"query": None, "states": [{}], "after": None, "limit": 2},
        ),
        ("asset.get", {"asset_id": True}),
    ],
)
def test_runtime_rejects_expanded_or_invalid_payloads(
    capability_id: str, parameters: dict[str, Any]
) -> None:
    env, _ = _fixture()
    with pytest.raises(Failure) as caught:
        _dispatch(env, capability_id, parameters)
    assert caught.value.code == "bridge_protocol_error"
