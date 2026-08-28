from __future__ import annotations

from copy import deepcopy

import pytest

from odoo_accounting_cli_v4.bridge.account_returns_runtime import dispatch


class Failure(RuntimeError):
    def __init__(self, code: str, message: str, *, exit_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


class Registry:
    def __init__(self, missing: str | None = None) -> None:
        self.missing = missing

    def get(self, model: str):
        return None if model == self.missing else object()


class User:
    def __init__(self, allowed: bool = True) -> None:
        self.allowed = allowed

    def has_group(self, name: str) -> bool:
        assert name == "account.group_account_readonly"
        return self.allowed


class Model:
    def __init__(
        self,
        *,
        fields: set[str] = frozenset(),
        rows: list[dict] | None = None,
        access: bool = True,
        count: int | None = None,
        counts: list[tuple[tuple, int]] | None = None,
        cursor_exists: bool = True,
        company_model: bool = False,
    ) -> None:
        self._fields = {field: object() for field in fields}
        self.rows = deepcopy(rows or [])
        self.access = access
        self.count = len(self.rows) if count is None else count
        self.counts = list(counts or [])
        self.cursor_exists = cursor_exists
        self.company_model = company_model
        self.contexts: list[dict] = []
        self.companies: list[int] = []
        self.search_count_calls: list[tuple[list, int | None]] = []
        self.search_read_calls: list[dict] = []

    def with_context(self, **context):
        self.contexts.append(context)
        return self

    def with_company(self, company_id: int):
        self.companies.append(company_id)
        return self

    def has_access(self, operation: str) -> bool:
        assert operation == "read"
        return self.access

    def search_count(self, domain: list, limit: int | None = None) -> int:
        copied = deepcopy(domain)
        self.search_count_calls.append((copied, limit))
        if not self.company_model and any(
            term[0] == "id" and term[1] == "=" for term in domain
        ):
            return int(self.cursor_exists)
        for required_terms, value in self.counts:
            if all(term in domain for term in required_terms):
                return value
        return self.count

    def search_read(
        self, domain: list, fields: list[str], *, order: str, limit: int
    ) -> list[dict]:
        self.search_read_calls.append(
            {
                "domain": deepcopy(domain),
                "fields": list(fields),
                "order": order,
                "limit": limit,
            }
        )
        return deepcopy(self.rows[:limit])


RETURN_FIELDS = {
    "name",
    "active",
    "date_from",
    "date_to",
    "date_deadline",
    "date_submission",
    "date_lock",
    "type_id",
    "state",
    "next_state",
    "is_completed",
    "company_id",
    "tax_unit_id",
    "manually_created",
    "check_count",
    "unresolved_check_count",
    "resolved_check_count",
    "check_ids",
}
TYPE_FIELDS = {
    "name",
    "category",
    "report_id",
    "country_id",
    "auto_generate",
    "states_workflow",
    "deadline_periodicity",
    "deadline_start_date",
    "deadline_days_delay",
}
CHECK_FIELDS = {
    "return_id",
    "code",
    "type",
    "name",
    "message",
    "state",
    "result",
    "records_count",
}


def _raw_return(return_id: int = 30) -> dict:
    return {
        "id": return_id,
        "name": "August manual return",
        "active": True,
        "date_from": "2026-08-01",
        "date_to": "2026-08-31",
        "date_deadline": "2026-09-15",
        "date_submission": False,
        "date_lock": False,
        "type_id": [4, "Manual Return"],
        "state": "new",
        "next_state": "reviewed",
        "is_completed": False,
        "company_id": [7, "China Company"],
        "tax_unit_id": False,
        "manually_created": True,
        "check_count": 1,
        "unresolved_check_count": 1,
        "resolved_check_count": 0,
    }


def _raw_type(type_id: int = 4) -> dict:
    return {
        "id": type_id,
        "name": "Manual Return",
        "category": "account_return",
        "report_id": False,
        "country_id": False,
        "auto_generate": True,
        "states_workflow": "generic_state_review",
        "deadline_periodicity": "year",
        "deadline_start_date": "2026-01-01",
        "deadline_days_delay": 15,
    }


def _raw_check(check_id: int = 50) -> dict:
    return {
        "id": check_id,
        "return_id": [30, "August manual return"],
        "code": "manual_check",
        "type": "check",
        "name": "Review manual return",
        "message": False,
        "state": "new",
        "result": "todo",
        "records_count": 0,
    }


class Env:
    def __init__(
        self,
        *,
        returns: Model | None = None,
        return_types: Model | None = None,
        checks: Model | None = None,
        company_visible: bool = True,
        group_allowed: bool = True,
        missing_model: str | None = None,
    ) -> None:
        self.uid = 5
        self.user = User(group_allowed)
        self.registry = Registry(missing_model)
        self.models = {
            "res.company": Model(count=int(company_visible), company_model=True),
            "account.return": returns or Model(fields=RETURN_FIELDS),
            "account.return.type": return_types or Model(fields=TYPE_FIELDS),
            "account.return.check": checks or Model(fields=CHECK_FIELDS),
            "account.tax.unit": Model(),
            "account.report": Model(),
            "res.country": Model(),
        }

    def __getitem__(self, name: str) -> Model:
        return self.models[name]


def _payload(capability_id: str, parameters: dict) -> dict:
    return {
        "capability_id": capability_id,
        "company_id": 7,
        "parameters": parameters,
    }


def _search_parameters(**overrides) -> dict:
    value = {
        "type_id": None,
        "state": None,
        "completed": None,
        "deadline_from": None,
        "deadline_to": None,
        "active": True,
        "after": None,
        "limit": 101,
    }
    value.update(overrides)
    return value


def test_search_uses_fixed_company_filters_id_cursor_and_type_context() -> None:
    returns = Model(fields=RETURN_FIELDS, rows=[_raw_return(29)])
    return_types = Model(fields=TYPE_FIELDS, rows=[_raw_type()])
    env = Env(returns=returns, return_types=return_types)
    parameters = _search_parameters(
        type_id=4,
        state="new",
        completed=False,
        deadline_from="2026-08-01",
        deadline_to="2026-09-30",
        after=30,
        limit=11,
    )

    page = dispatch(
        env,
        _payload("account.return.search", parameters),
        7,
        failure_type=Failure,
    )

    assert page["items"][0]["id"] == 29
    assert page["items"][0]["company_id"] == 7
    assert page["items"][0]["type"]["category"] == "account_return"
    call = returns.search_read_calls[0]
    assert call["order"] == "id desc"
    assert call["limit"] == 11
    for term in (
        ("company_id", "=", 7),
        ("type_id", "=", 4),
        ("state", "=", "new"),
        ("is_completed", "=", False),
        ("date_deadline", ">=", "2026-08-01"),
        ("date_deadline", "<=", "2026-09-30"),
        ("active", "=", True),
        ("id", "<", 30),
    ):
        assert term in call["domain"]
    assert return_types.companies == [7]
    assert return_types.contexts == [{"allowed_company_ids": [7], "active_test": False}]


def test_summary_uses_only_fixed_active_counts_and_required_as_of() -> None:
    returns = Model(
        fields=RETURN_FIELDS,
        counts=[
            ((("is_completed", "=", True),), 1),
            (
                (
                    ("is_completed", "=", False),
                    ("date_deadline", "<", "2026-08-28"),
                ),
                1,
            ),
            (
                (
                    ("is_completed", "=", False),
                    ("date_deadline", "=", "2026-08-28"),
                ),
                1,
            ),
            (
                (
                    ("is_completed", "=", False),
                    ("date_deadline", ">", "2026-08-28"),
                    ("date_deadline", "<=", "2026-09-27"),
                ),
                1,
            ),
            (
                (
                    ("is_completed", "=", False),
                    ("date_deadline", ">", "2026-09-27"),
                ),
                1,
            ),
            ((("is_completed", "=", False),), 4),
        ],
        count=5,
    )
    page = dispatch(
        Env(returns=returns),
        _payload("account.return.summary", {"as_of": "2026-08-28"}),
        7,
        failure_type=Failure,
    )

    assert page["items"] == [
        {
            "company_id": 7,
            "as_of": "2026-08-28",
            "counts": {
                "total": 5,
                "open": 4,
                "completed": 1,
                "overdue": 1,
                "due_today": 1,
                "due_next_30_days": 1,
                "later": 1,
            },
        }
    ]
    assert len(returns.search_count_calls) == 7
    assert all(
        ("company_id", "=", 7) in domain and ("active", "=", True) in domain
        for domain, _limit in returns.search_count_calls
    )


def test_type_list_reads_company_dependent_values_with_company() -> None:
    return_types = Model(fields=TYPE_FIELDS, rows=[_raw_type()])
    page = dispatch(
        Env(return_types=return_types),
        _payload(
            "account.return.type.list",
            {"category": "account_return", "after": None, "limit": 101},
        ),
        7,
        failure_type=Failure,
    )

    assert page["items"][0]["company_id"] == 7
    assert page["items"][0]["deadline_days_delay"] == 15
    assert return_types.companies == [7]
    assert return_types.search_read_calls[0]["domain"] == [
        ("category", "=", "account_return")
    ]


def test_check_list_and_get_are_bounded_by_a_visible_return() -> None:
    returns = Model(
        fields=RETURN_FIELDS, rows=[{"id": 30, "name": "August manual return"}]
    )
    checks = Model(fields=CHECK_FIELDS, rows=[_raw_check()])
    env = Env(returns=returns, checks=checks)

    listed = dispatch(
        env,
        _payload(
            "account.return.check.list",
            {
                "return_id": 30,
                "result": "todo",
                "type": "check",
                "after": None,
                "limit": 101,
            },
        ),
        7,
        failure_type=Failure,
    )
    assert listed["items"][0]["return"] == {
        "id": 30,
        "name": "August manual return",
    }
    assert set(listed["items"][0]).isdisjoint({"action", "attachment_ids"})
    assert ("company_id", "=", 7) in returns.search_read_calls[0]["domain"]
    assert checks.search_read_calls[0]["domain"] == [
        ("return_id", "=", 30),
        ("result", "=", "todo"),
        ("type", "=", "check"),
    ]

    returns.search_read_calls.clear()
    checks.search_read_calls.clear()
    fetched = dispatch(
        env,
        _payload("account.return.check.get", {"check_id": 50}),
        7,
        failure_type=Failure,
    )
    assert fetched["items"][0]["id"] == 50
    assert ("check_ids", "in", [50]) in returns.search_read_calls[0]["domain"]
    assert checks.search_read_calls[0]["domain"] == [
        ("id", "=", 50),
        ("return_id", "=", 30),
    ]


@pytest.mark.parametrize(
    "env",
    [
        Env(company_visible=False),
        Env(group_allowed=False),
        Env(missing_model="account.return"),
        Env(returns=Model(fields=RETURN_FIELDS, access=False)),
    ],
)
def test_scope_failures_return_closed_empty_page(env: Env) -> None:
    page = dispatch(
        env,
        _payload("account.return.search", _search_parameters()),
        7,
        failure_type=Failure,
    )
    assert page["items"] == []
    assert page["access_allowed"] is False


def test_payload_and_required_field_drift_fail_closed() -> None:
    payload = _payload("account.return.search", _search_parameters())
    payload["extra"] = True
    with pytest.raises(Failure) as caught:
        dispatch(Env(), payload, 7, failure_type=Failure)
    assert caught.value.code == "bridge_protocol_error"

    with pytest.raises(Failure) as caught:
        dispatch(
            Env(returns=Model(fields=RETURN_FIELDS - {"company_id"})),
            _payload("account.return.search", _search_parameters()),
            7,
            failure_type=Failure,
        )
    assert caught.value.code == "odoo_runtime_error"
