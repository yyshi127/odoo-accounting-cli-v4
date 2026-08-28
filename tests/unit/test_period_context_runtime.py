from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge import period_context_runtime as period


class Failure(RuntimeError):
    def __init__(self, code: str, message: str, *, exit_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


class Records(list):
    @property
    def ids(self) -> list[int]:
        return [record.id for record in self]


def _related_id(value: Any) -> Any:
    return getattr(value, "id", value)


def _comparable(value: Any) -> Any:
    return value.isoformat() if isinstance(value, date) else _related_id(value)


def _term_matches(row: Any, term: tuple[str, str, Any]) -> bool:
    field, operator, expected = term
    actual = _comparable(getattr(row, field))
    if operator == "=":
        return actual == expected
    if operator == "<":
        return actual < expected
    if operator == "<=":
        return actual <= expected
    if operator == ">=":
        return actual >= expected
    raise AssertionError(f"unsupported fake-domain operator: {operator}")


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
        try:
            seek_index = domain.index("|")
        except ValueError:
            seek_index = len(domain)
        if not all(_term_matches(row, term) for term in domain[:seek_index]):
            return False
        if seek_index == len(domain):
            return True
        before_date = domain[seek_index + 1][2]
        same_date = domain[seek_index + 3][2]
        before_id = domain[seek_index + 4][2]
        assert before_date == same_date
        row_date = _comparable(row.date_from)
        return row_date < before_date or (
            row_date == same_date and row.id < before_id
        )

    def search_count(self, domain: list[Any], *, limit: int) -> int:
        self.calls.append(("search_count", domain, limit))
        return min(limit, sum(self._matches(row, domain) for row in self.rows))

    def search(
        self,
        domain: list[Any],
        *,
        limit: int,
        order: str | None = None,
    ) -> Records:
        self.calls.append(("search", domain, order, limit))
        rows = [row for row in self.rows if self._matches(row, domain)]
        if order == "date_from desc, id desc":
            rows.sort(
                key=lambda row: (_comparable(row.date_from), row.id), reverse=True
            )
        return Records(rows[:limit])


class CompanyRecord(SimpleNamespace):
    def compute_fiscalyear_dates(self, target: date) -> dict[str, Any]:
        self.resolve_calls.append(target)
        return self.resolution


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
    company = CompanyRecord(
        id=7,
        fiscalyear_lock_date=date(2025, 12, 31),
        tax_lock_date=False,
        sale_lock_date=date.min,
        purchase_lock_date=None,
        hard_lock_date=date(2026, 1, 31),
        user_fiscalyear_lock_date=date(2025, 12, 31),
        user_tax_lock_date=date.min,
        user_sale_lock_date=date.min,
        user_purchase_lock_date=date.min,
        user_hard_lock_date=date(2026, 1, 31),
        resolve_calls=[],
        resolution={},
    )
    other_company = CompanyRecord(id=8)
    fiscal_2026 = SimpleNamespace(
        id=12,
        name="2026",
        company_id=company,
        date_from=date(2026, 1, 1),
        date_to=date(2026, 12, 31),
    )
    fiscal_2025 = SimpleNamespace(
        id=11,
        name="2025",
        company_id=company,
        date_from=date(2025, 1, 1),
        date_to=date(2025, 12, 31),
    )
    other_fiscal = SimpleNamespace(
        id=99,
        name="Other 2026",
        company_id=other_company,
        date_from=date(2026, 1, 1),
        date_to=date(2026, 12, 31),
    )
    company.resolution = {
        "date_from": date(2026, 1, 1),
        "date_to": date(2026, 12, 31),
        "record": fiscal_2026,
    }
    lock_fields = set(period._LOCK_FIELDS) | set(period._LOCK_FIELDS.values())
    models = {
        "res.company": Model([company, other_company], fields=lock_fields),
        "account.fiscal.year": Model(
            [fiscal_2025, other_fiscal, fiscal_2026],
            fields=set(period._FISCAL_YEAR_FIELDS),
        ),
    }
    return Env(models), {
        "company": company,
        "fiscal_2026": fiscal_2026,
        "fiscal_2025": fiscal_2025,
    }


def _dispatch(
    env: Env, capability_id: str, parameters: dict[str, Any]
) -> dict[str, Any]:
    return period.dispatch(
        env,
        {
            "capability_id": capability_id,
            "company_id": 7,
            "parameters": parameters,
        },
        7,
        failure_type=Failure,
    )


def _search_parameters(**overrides: Any) -> dict[str, Any]:
    value = {
        "contains_date": None,
        "date_from": None,
        "date_to": None,
        "after": None,
        "limit": 3,
    }
    value.update(overrides)
    return value


def test_lock_inspect_normalizes_false_none_and_date_min_to_null() -> None:
    env, _ = _fixture()

    page = _dispatch(env, "company.lock_dates.inspect", {})

    assert page["items"] == [
        {
            "company_id": 7,
            "configured": {
                "fiscalyear_lock_date": "2025-12-31",
                "tax_lock_date": None,
                "sale_lock_date": None,
                "purchase_lock_date": None,
                "hard_lock_date": "2026-01-31",
            },
            "effective": {
                "fiscalyear_lock_date": "2025-12-31",
                "tax_lock_date": None,
                "sale_lock_date": None,
                "purchase_lock_date": None,
                "hard_lock_date": "2026-01-31",
            },
        }
    ]


def test_resolve_calls_native_compute_fiscalyear_dates_without_sudo() -> None:
    env, records = _fixture()

    page = _dispatch(
        env, "company.fiscal_year.resolve", {"date": "2026-08-28"}
    )

    assert records["company"].resolve_calls == [date(2026, 8, 28)]
    assert page["items"] == [
        {
            "company_id": 7,
            "date": "2026-08-28",
            "date_from": "2026-01-01",
            "date_to": "2026-12-31",
            "fiscal_year": {"id": 12, "name": "2026"},
        }
    ]
    assert not any(
        call[0] == "sudo"
        for model in env.models.values()
        for call in model.calls
    )


def test_search_forces_company_filters_and_fixed_date_id_order() -> None:
    env, _ = _fixture()

    page = _dispatch(
        env,
        "fiscal_year.search",
        _search_parameters(contains_date="2026-08-28"),
    )

    assert [item["id"] for item in page["items"]] == [12]
    search_call = next(
        call
        for call in env.models["account.fiscal.year"].calls
        if call[0] == "search"
    )
    assert ("company_id", "=", 7) in search_call[1]
    assert ("date_from", "<=", "2026-08-28") in search_call[1]
    assert ("date_to", ">=", "2026-08-28") in search_call[1]
    assert search_call[2:] == ("date_from desc, id desc", 3)


def test_search_cursor_anchor_must_exist_in_the_same_company_and_filter_scope() -> None:
    env, _ = _fixture()
    page = _dispatch(
        env,
        "fiscal_year.search",
        _search_parameters(after=["2026-01-01", 12]),
    )

    assert page["cursor_found"] is True
    assert [item["id"] for item in page["items"]] == [11]
    anchor_call = next(
        call
        for call in env.models["account.fiscal.year"].calls
        if call[0] == "search_count"
        and ("id", "=", 12) in call[1]
    )
    assert ("company_id", "=", 7) in anchor_call[1]
    assert ("date_from", "=", "2026-01-01") in anchor_call[1]

    missing = _dispatch(
        env,
        "fiscal_year.search",
        _search_parameters(after=["2026-01-01", 99]),
    )
    assert missing["cursor_found"] is False
    assert missing["items"] == []


def test_get_never_returns_another_company_fiscal_year() -> None:
    env, _ = _fixture()

    assert _dispatch(env, "fiscal_year.get", {"fiscal_year_id": 12})["items"][
        0
    ]["company_id"] == 7
    assert _dispatch(env, "fiscal_year.get", {"fiscal_year_id": 99})["items"] == []
    assert _dispatch(env, "fiscal_year.get", {"fiscal_year_id": 999})["items"] == []


def test_acl_denial_and_missing_fiscal_year_model_fail_closed() -> None:
    env, _ = _fixture()
    env.models["account.fiscal.year"].access = False

    denied = {
        "user_id": 5,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": False,
        "cursor_found": True,
        "items": [],
    }
    assert _dispatch(env, "fiscal_year.search", _search_parameters()) == denied
    assert _dispatch(
        env, "company.fiscal_year.resolve", {"date": "2026-08-28"}
    ) == denied

    env, _ = _fixture()
    del env.models["account.fiscal.year"]
    page = _dispatch(env, "fiscal_year.get", {"fiscal_year_id": 12})
    assert page["module_installed"] is False
    assert page["access_allowed"] is False
    resolve_page = _dispatch(
        env, "company.fiscal_year.resolve", {"date": "2026-08-28"}
    )
    assert resolve_page["module_installed"] is False
    assert resolve_page["access_allowed"] is False


def test_required_field_drift_and_cross_company_resolution_fail_closed() -> None:
    env, _ = _fixture()
    del env.models["account.fiscal.year"]._fields["date_to"]
    with pytest.raises(Failure) as caught:
        _dispatch(env, "fiscal_year.search", _search_parameters())
    assert caught.value.code == "odoo_runtime_error"

    env, records = _fixture()
    records["company"].resolution["record"].company_id = SimpleNamespace(id=8)
    with pytest.raises(Failure) as caught:
        _dispatch(
            env, "company.fiscal_year.resolve", {"date": "2026-08-28"}
        )
    assert caught.value.code == "odoo_runtime_error"


@pytest.mark.parametrize(
    ("capability_id", "parameters"),
    [
        ("company.lock_dates.inspect", {"extra": True}),
        ("company.fiscal_year.resolve", {"date": "2026-02-30"}),
        ("fiscal_year.get", {"fiscal_year_id": True}),
        ("fiscal_year.search", {"contains_date": None}),
        ("fiscal_year.search", _search_parameters(limit=1002)),
        ("fiscal_year.search", _search_parameters(after=["2026-01-01", True])),
    ],
)
def test_runtime_rejects_expanded_or_invalid_payloads(
    capability_id: str, parameters: dict[str, Any]
) -> None:
    env, _ = _fixture()
    with pytest.raises(Failure) as caught:
        _dispatch(env, capability_id, parameters)
    assert caught.value.code == "bridge_protocol_error"
