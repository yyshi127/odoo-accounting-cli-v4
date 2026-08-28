from __future__ import annotations

import copy
from datetime import date
from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge import runtime
from odoo_accounting_cli_v4.bridge.runtime import RuntimeFailure

ACTION = "res.currency.rate.read_page"
RATE_FIELDS = [
    "id",
    "name",
    "currency_id",
    "company_id",
    "rate",
    "company_rate",
    "inverse_company_rate",
]
COMPANY_FIELDS = ["id", "root_id", "currency_id"]
CURRENCY_FIELDS = ["id", "name"]


def _filters(**overrides: Any) -> dict[str, Any]:
    value = {"date_from": None, "date_to": None, "currency_id": None}
    value.update(overrides)
    return value


def _payload(**overrides: Any) -> dict[str, Any]:
    value = {
        "company_id": 7,
        "after": None,
        "limit": 3,
        "filters": _filters(),
    }
    value.update(overrides)
    return value


def _reference_id(value: Any) -> int | None:
    if value in (False, None):
        return None
    return value[0] if isinstance(value, (list, tuple)) else value


def _project(row: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    return {field: copy.deepcopy(row[field]) for field in dict.fromkeys(["id", *fields])}


class _Model:
    def __init__(self, name: str, env: "_Environment") -> None:
        self.name = name
        self.env = env

    def has_access(self, operation: str) -> bool:
        self.env.calls.append(("access", self.name, operation))
        return self.env.denied_model != self.name

    def browse(self, record_id: int):
        self.env.calls.append(("browse", self.name, record_id))
        assert self.name == "res.users"
        assert record_id == self.env.uid
        return _User(self.env)

    def with_context(self, **context: Any):
        self.env.calls.append(("context", self.name, copy.deepcopy(context)))
        assert context == {"active_test": False, "allowed_company_ids": [7]}
        return self

    def search_count(self, domain: list[Any], *, limit: int) -> int:
        self.env.calls.append(("count", self.name, copy.deepcopy(domain), limit))
        return int(self.env.company_visible)

    def search_read(
        self,
        domain: list[Any],
        *,
        fields: list[str],
        limit: int | None = None,
        order: str | None = None,
    ) -> list[dict[str, Any]]:
        self.env.calls.append(
            ("search", self.name, copy.deepcopy(domain), list(fields), limit, order)
        )
        if self.name == "res.currency.rate":
            rows = copy.deepcopy(self.env.rate_rows)
            for term in domain:
                if not isinstance(term, tuple):
                    continue
                field, operator, value = term
                if field == "currency_id" and operator == "=":
                    rows = [
                        row
                        for row in rows
                        if _reference_id(row["currency_id"]) == value
                    ]
                elif field == "name" and operator == ">=":
                    rows = [row for row in rows if row["name"] >= value]
                elif field == "name" and operator == "<=":
                    rows = [row for row in rows if row["name"] <= value]
        elif self.name == "res.company":
            ids = next(
                (
                    term[2]
                    for term in domain
                    if isinstance(term, tuple) and term[:2] == ("id", "in")
                ),
                None,
            )
            exact_id = next(
                (
                    term[2]
                    for term in domain
                    if isinstance(term, tuple) and term[:2] == ("id", "=")
                ),
                None,
            )
            rows = copy.deepcopy(self.env.company_rows)
            if ids is not None:
                rows = [row for row in rows if row["id"] in ids]
            if exact_id is not None:
                rows = [row for row in rows if row["id"] == exact_id]
                if exact_id == 7 and not self.env.company_visible:
                    rows = []
        else:
            ids = next(
                term[2]
                for term in domain
                if isinstance(term, tuple) and term[:2] == ("id", "in")
            )
            rows = [
                copy.deepcopy(row)
                for row in self.env.currency_rows
                if row["id"] in ids
            ]
        if limit is not None:
            rows = rows[:limit]
        return [_project(row, fields) for row in rows]

    def sudo(self, *args: Any, **kwargs: Any):
        raise AssertionError(f"currency-rate runtime must never sudo {self.name}")


class _Registry:
    def __init__(self, env: "_Environment") -> None:
        self.env = env

    def get(self, model: str):
        self.env.calls.append(("registry", model))
        assert model in {
            "res.company",
            "res.currency.rate",
            "res.currency",
            "res.users",
        }
        return None if self.env.missing_model == model else self.env.models[model]


class _User:
    def __init__(self, env: "_Environment") -> None:
        self.env = env

    @property
    def id(self) -> int:
        return self.env.uid

    def has_group(self, xml_id: str) -> bool:
        self.env.calls.append(("group", xml_id))
        assert xml_id == "base.group_user"
        return self.env.group_member


class _Environment:
    uid = 42
    su = False

    def __init__(
        self,
        *,
        company_visible: bool = True,
        missing_model: str | None = None,
        denied_model: str | None = None,
        group_member: bool = True,
    ) -> None:
        self.calls: list[tuple[Any, ...]] = []
        self.company_visible = company_visible
        self.missing_model = missing_model
        self.denied_model = denied_model
        self.group_member = group_member
        self.company_rows = [
            {"id": 7, "root_id": [1, "Root"], "currency_id": [6, "CNY"]},
            {"id": 1, "root_id": [1, "Root"], "currency_id": [6, "CNY"]},
        ]
        self.rate_rows = [
            {
                "id": 13,
                "name": "2025-02-01",
                "currency_id": [2, "untrusted USD"],
                "company_id": [1, "untrusted Root"],
                "rate": 0.7299270072992701,
                "company_rate": 0.7299270072992701,
                "inverse_company_rate": 1.37,
            },
            {
                "id": 14,
                "name": "2025-02-01",
                "currency_id": [3, "untrusted EUR"],
                "company_id": False,
                "rate": 0.8,
                "company_rate": 0.8,
                "inverse_company_rate": 1.25,
            },
        ]
        self.currency_rows = [
            {"id": 2, "name": "USD"},
            {"id": 3, "name": "EUR"},
            {"id": 6, "name": "CNY"},
        ]
        self.models = {
            model: _Model(model, self)
            for model in (
                "res.company",
                "res.currency.rate",
                "res.currency",
                "res.users",
            )
        }
        self.registry = _Registry(self)

    @property
    def user(self):
        raise AssertionError("currency-rate runtime must not use sudoed env.user")

    def __getitem__(self, model: str):
        self.calls.append(("model", model))
        if model not in self.models:
            raise AssertionError(f"unexpected model access: {model}")
        return self.models[model]


def _search_calls(env: _Environment, model: str) -> list[tuple[Any, ...]]:
    return [call for call in env.calls if call[:2] == ("search", model)]


def test_currency_rate_page_freezes_root_global_scope_order_and_decimal_directions() -> None:
    env = _Environment()

    result = runtime._dispatch(
        env,
        ACTION,
        _payload(
            after=["2025-02-15", 11],
            filters=_filters(
                date_from="2025-01-01", date_to="2025-12-31"
            ),
        ),
        7,
    )

    assert result == {
        "user_id": 42,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "root_company_id": 1,
        "rows": [
            {
                "id": 13,
                "date": "2025-02-01",
                "currency": {"id": 2, "code": "USD"},
                "company_currency": {"id": 6, "code": "CNY"},
                "requested_company_id": 7,
                "source_company_id": 1,
                "technical_rate": "0.7299270072992701",
                "foreign_units_per_company_unit": "0.7299270072992701",
                "company_units_per_foreign_unit": "1.37",
            },
            {
                "id": 14,
                "date": "2025-02-01",
                "currency": {"id": 3, "code": "EUR"},
                "company_currency": {"id": 6, "code": "CNY"},
                "requested_company_id": 7,
                "source_company_id": None,
                "technical_rate": "0.8",
                "foreign_units_per_company_unit": "0.8",
                "company_units_per_foreign_unit": "1.25",
            },
        ],
    }
    assert ACTION in runtime._ACTIONS
    assert ("registry", "res.company") in env.calls
    assert ("registry", "res.currency.rate") in env.calls
    assert ("registry", "res.currency") in env.calls
    for model in ("res.company", "res.currency.rate", "res.currency", "res.users"):
        assert ("access", model, "read") in env.calls
        if model != "res.users":
            assert (
                "context",
                model,
                {"active_test": False, "allowed_company_ids": [7]},
            ) in env.calls
    assert ("browse", "res.users", 42) in env.calls
    assert ("group", "base.group_user") in env.calls

    expected_domain = [
        "&",
        "&",
        "&",
        "|",
        ("company_id", "=", False),
        ("company_id", "=", 1),
        ("name", ">=", "2025-01-01"),
        ("name", "<=", "2025-12-31"),
        "|",
        ("name", "<", "2025-02-15"),
        "&",
        ("name", "=", "2025-02-15"),
        ("id", ">", 11),
    ]
    assert _search_calls(env, "res.currency.rate") == [
        ("search", "res.currency.rate", expected_domain, RATE_FIELDS, 3, "name desc,id")
    ]
    assert _search_calls(env, "res.company") == [
        ("search", "res.company", [("id", "=", 7)], COMPANY_FIELDS, 1, "id"),
    ]
    assert _search_calls(env, "res.currency") == [
        (
            "search",
            "res.currency",
            [("id", "in", [2, 3, 6])],
            CURRENCY_FIELDS,
            3,
            "id",
        )
    ]


def test_currency_rate_currency_filter_is_part_of_the_orm_domain() -> None:
    env = _Environment()

    result = runtime._dispatch(
        env,
        ACTION,
        _payload(filters=_filters(currency_id=2)),
        7,
    )

    assert _search_calls(env, "res.currency.rate")[0][2] == [
        "&",
        "|",
        ("company_id", "=", False),
        ("company_id", "=", 1),
        ("currency_id", "=", 2),
    ]
    assert [row["currency"]["id"] for row in result["rows"]] == [2]


def test_currency_rate_first_page_has_only_root_global_scope() -> None:
    env = _Environment()

    runtime._dispatch(env, ACTION, _payload(), 7)

    assert _search_calls(env, "res.currency.rate")[0] == (
        "search",
        "res.currency.rate",
        ["|", ("company_id", "=", False), ("company_id", "=", 1)],
        RATE_FIELDS,
        3,
        "name desc,id",
    )


def test_currency_rate_page_normalizes_odoo_date_values() -> None:
    env = _Environment()
    for row in env.rate_rows:
        row["name"] = date.fromisoformat(row["name"])

    result = runtime._dispatch(env, ACTION, _payload(), 7)

    assert [row["date"] for row in result["rows"]] == [
        "2025-02-01",
        "2025-02-01",
    ]


@pytest.mark.parametrize(
    ("company_visible", "missing_model", "denied_model", "group_member", "expected"),
    (
        (False, None, None, True, (False, True, True)),
        (True, "res.company", None, True, (False, False, False)),
        (True, "res.currency.rate", None, True, (False, False, False)),
        (True, "res.currency", None, True, (False, False, False)),
        (True, "res.users", None, True, (False, False, False)),
        (True, None, "res.company", True, (False, True, False)),
        (True, None, "res.currency.rate", True, (False, True, False)),
        (True, None, "res.currency", True, (False, True, False)),
        (True, None, "res.users", True, (False, True, False)),
        (True, None, None, False, (False, True, False)),
    ),
)
def test_currency_rate_page_gates_company_model_and_all_read_acls(
    company_visible: bool,
    missing_model: str | None,
    denied_model: str | None,
    group_member: bool,
    expected: tuple[bool, bool, bool],
) -> None:
    env = _Environment(
        company_visible=company_visible,
        missing_model=missing_model,
        denied_model=denied_model,
        group_member=group_member,
    )

    result = runtime._dispatch(env, ACTION, _payload(), 7)

    assert (
        result["company_visible"],
        result["module_installed"],
        result["access_allowed"],
    ) == expected
    assert result["root_company_id"] is None
    assert result["rows"] == []
    assert not _search_calls(env, "res.currency.rate")
    if missing_model is None and denied_model is None:
        assert ("group", "base.group_user") in env.calls


@pytest.mark.parametrize(
    "payload",
    (
        {"company_id": 7, "after": None, "limit": 3},
        {**_payload(), "model": "res.users"},
        _payload(company_id=True),
        _payload(limit=True),
        _payload(limit=0),
        _payload(limit=1002),
        _payload(after={}),
        _payload(after=["2025-01-01"]),
        _payload(after=["2025-01-01", True]),
        _payload(after=["2025-01-01", 0]),
        _payload(after=["2025-1-1", 2]),
        _payload(filters={}),
        _payload(filters={**_filters(), "query": "USD"}),
        _payload(filters=_filters(date_from=True)),
        _payload(filters=_filters(date_from="2025-1-1")),
        _payload(filters=_filters(date_to="2025-02-30")),
        _payload(filters=_filters(date_from="2025-02-01", date_to="2025-01-01")),
        _payload(filters=_filters(currency_id=True)),
        _payload(filters=_filters(currency_id=0)),
    ),
)
def test_currency_rate_payload_fails_closed(payload: dict[str, Any]) -> None:
    with pytest.raises(RuntimeFailure) as caught:
        runtime._dispatch(_Environment(), ACTION, payload, 7)

    assert caught.value.code == "bridge_protocol_error"
    assert caught.value.exit_code == 7


def test_currency_rate_company_mismatch_fails_closed_before_model_access() -> None:
    env = _Environment()

    with pytest.raises(RuntimeFailure) as caught:
        runtime._dispatch(env, ACTION, _payload(company_id=8), 7)

    assert caught.value.code == "company_unavailable"
    assert caught.value.exit_code == 3
    assert not env.calls


@pytest.mark.parametrize(
    "mutation",
    (
        "wrong_target_root",
        "missing_currency",
        "duplicate_currency",
        "invalid_date",
        "unexpected_source",
        "invalid_rate_reference",
    ),
)
def test_currency_rate_related_reread_and_raw_rows_fail_closed(mutation: str) -> None:
    env = _Environment()
    if mutation == "wrong_target_root":
        env.company_rows[0]["root_id"] = [9, "Wrong"]
    elif mutation == "missing_currency":
        env.currency_rows = [row for row in env.currency_rows if row["id"] != 2]
    elif mutation == "duplicate_currency":
        env.currency_rows[1] = {"id": 2, "name": "USD"}
    elif mutation == "invalid_date":
        env.rate_rows[0]["name"] = "2025-2-1"
    elif mutation == "unexpected_source":
        env.rate_rows[0]["company_id"] = [9, "Other"]
    else:
        env.rate_rows[0]["currency_id"] = False

    with pytest.raises(RuntimeFailure) as caught:
        runtime._dispatch(env, ACTION, _payload(), 7)

    assert caught.value.code == "odoo_runtime_error"
    assert caught.value.exit_code == 7


def test_currency_rate_business_directions_must_be_reciprocal() -> None:
    env = _Environment()
    env.rate_rows[0]["company_rate"] = 0.5

    with pytest.raises(RuntimeFailure) as caught:
        runtime._dispatch(env, ACTION, _payload(), 7)

    assert caught.value.code == "odoo_runtime_error"
    assert caught.value.exit_code == 7


@pytest.mark.parametrize(
    "field",
    ("rate", "company_rate", "inverse_company_rate"),
)
@pytest.mark.parametrize("value", [True, 0, -1, float("nan"), float("inf")])
def test_currency_rate_numeric_values_must_be_finite_and_positive(
    field: str, value: Any
) -> None:
    env = _Environment()
    env.rate_rows[0][field] = value

    with pytest.raises(RuntimeFailure) as caught:
        runtime._dispatch(env, ACTION, _payload(), 7)

    assert caught.value.code == "odoo_runtime_error"
    assert caught.value.exit_code == 7
