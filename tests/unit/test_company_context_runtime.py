from __future__ import annotations

import copy
from types import SimpleNamespace

import pytest

from odoo_accounting_cli_v4.bridge import runtime
from odoo_accounting_cli_v4.bridge.runtime import RuntimeFailure


_RAW_COMPANIES = [
    {
        "id": 7,
        "name": "China Company",
        "sequence": 0,
        "active": True,
        "currency_id": [6, "CNY"],
        "country_id": [48, "China"],
        "account_fiscal_country_id": [48, "China"],
        "chart_template": "cn_oscg",
        "tax_calculation_rounding_method": "round_globally",
        "fiscalyear_last_month": "12",
        "fiscalyear_last_day": 31,
    },
    {
        "id": 8,
        "name": "Singapore Company",
        "sequence": 10,
        "active": True,
        "currency_id": [37, "SGD"],
        "country_id": [197, "Singapore"],
        "account_fiscal_country_id": [197, "Singapore"],
        "chart_template": "sg",
        "tax_calculation_rounding_method": "round_globally",
        "fiscalyear_last_month": "12",
        "fiscalyear_last_day": 31,
    },
]


class _Registry:
    def __init__(self, installed: bool = True) -> None:
        self.installed = installed

    def get(self, model: str):
        return object() if self.installed and model == "account.account" else None


class _Model:
    def __init__(self, name: str, calls: list, *, access: bool = True) -> None:
        self.name = name
        self.calls = calls
        self.access = access

    def has_access(self, operation: str) -> bool:
        self.calls.append(("access", self.name, operation))
        return self.access

    def search_count(self, domain, *, limit: int) -> int:
        self.calls.append(("count", self.name, copy.deepcopy(domain), limit))
        return 1

    def with_context(self, **context):
        self.calls.append(("context", self.name, context))
        return self

    def search_read(self, domain, *, fields, limit: int, order: str):
        self.calls.append(
            (
                "search",
                self.name,
                copy.deepcopy(domain),
                tuple(fields),
                limit,
                order,
            )
        )
        if self.name == "res.company":
            after = next((term[2] for term in domain if term[:2] == ("id", ">")), 0)
            return [copy.deepcopy(row) for row in _RAW_COMPANIES if row["id"] > after][
                :limit
            ]
        if self.name == "res.currency":
            requested = set(domain[0][2])
            return [row for row in [
                {"id": 6, "name": "CNY", "decimal_places": 2},
                {"id": 37, "name": "SGD", "decimal_places": 2},
            ] if row["id"] in requested]
        if self.name == "res.country":
            requested = set(domain[0][2])
            return [row for row in [
                {"id": 48, "code": "CN", "name": "China"},
                {"id": 197, "code": "SG", "name": "Singapore"},
            ] if row["id"] in requested]
        raise AssertionError(self.name)


class _Environment:
    uid = 42

    def __init__(
        self,
        calls: list,
        *,
        installed: bool = True,
        denied_model: str | None = None,
    ) -> None:
        self.registry = _Registry(installed)
        self.models = {
            name: _Model(name, calls, access=name != denied_model)
            for name in ("res.company", "res.currency", "res.country")
        }

    def __getitem__(self, model: str) -> _Model:
        return self.models[model]


def _payload(*, after=None, limit: int = 3, company_id: int = 7) -> dict:
    return {"company_id": company_id, "after": after, "limit": limit}


def test_effective_company_ids_intersect_config_with_real_user_membership() -> None:
    users = SimpleNamespace(company_ids=SimpleNamespace(ids=[8, 7]))
    target = SimpleNamespace(company_id=7, available_company_ids=(7, 8, 9))

    assert runtime._effective_company_ids(users, target) == (7, 8)


def test_selected_company_must_belong_to_the_real_user() -> None:
    users = SimpleNamespace(company_ids=SimpleNamespace(ids=[8]))
    target = SimpleNamespace(company_id=7, available_company_ids=(7, 8))

    with pytest.raises(RuntimeFailure) as caught:
        runtime._effective_company_ids(users, target)

    assert caught.value.code == "company_unavailable"
    assert caught.value.exit_code == 3


def test_company_context_action_returns_only_configured_business_user_companies() -> None:
    calls: list = []

    result = runtime._dispatch(
        _Environment(calls),
        "res.company.accounting_context.read_page",
        _payload(),
        7,
        (7, 8),
    )

    assert result == {
        "user_id": 42,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "rows": [
            {
                "id": 7,
                "name": "China Company",
                "sequence": 0,
                "active": True,
                "chart_template": "cn_oscg",
                "tax_calculation_rounding_method": "round_globally",
                "currency": {"id": 6, "code": "CNY", "decimal_places": 2},
                "country": {"id": 48, "code": "CN", "name": "China"},
                "fiscal_country": {
                    "id": 48,
                    "code": "CN",
                    "name": "China",
                },
                "current": True,
                "fiscal_year_end": {"month": 12, "day": 31},
            },
            {
                "id": 8,
                "name": "Singapore Company",
                "sequence": 10,
                "active": True,
                "chart_template": "sg",
                "tax_calculation_rounding_method": "round_globally",
                "currency": {"id": 37, "code": "SGD", "decimal_places": 2},
                "country": {
                    "id": 197,
                    "code": "SG",
                    "name": "Singapore",
                },
                "fiscal_country": {
                    "id": 197,
                    "code": "SG",
                    "name": "Singapore",
                },
                "current": False,
                "fiscal_year_end": {"month": 12, "day": 31},
            },
        ],
    }
    company_search = next(
        call for call in calls if call[:2] == ("search", "res.company")
    )
    assert company_search[2] == [("id", "in", [7, 8])]
    assert company_search[-2:] == (3, "id")


def test_company_context_cursor_is_an_id_keyset_boundary() -> None:
    calls: list = []

    result = runtime._dispatch(
        _Environment(calls),
        "res.company.accounting_context.read_page",
        _payload(after=[7], limit=2),
        7,
        (7, 8),
    )

    assert [row["id"] for row in result["rows"]] == [8]
    company_search = next(
        call for call in calls if call[:2] == ("search", "res.company")
    )
    assert company_search[2] == [("id", "in", [7, 8]), ("id", ">", 7)]


@pytest.mark.parametrize(
    ("installed", "denied_model", "expected_installed"),
    [
        (False, None, False),
        (True, "res.company", True),
        (True, "res.currency", True),
        (True, "res.country", True),
    ],
)
def test_company_context_gate_fails_closed_without_read_access(
    installed: bool, denied_model: str | None, expected_installed: bool
) -> None:
    result = runtime._dispatch(
        _Environment([], installed=installed, denied_model=denied_model),
        "res.company.accounting_context.read_page",
        _payload(),
        7,
        (7, 8),
    )

    assert result["module_installed"] is expected_installed
    assert result["access_allowed"] is False
    assert result["rows"] == []


@pytest.mark.parametrize(
    ("payload", "available_company_ids", "code"),
    [
        ({"company_id": 7, "after": None}, (7, 8), "bridge_protocol_error"),
        (_payload(company_id=8), (7, 8), "company_unavailable"),
        (_payload(after=[]), (7, 8), "bridge_protocol_error"),
        (_payload(after=[True]), (7, 8), "bridge_protocol_error"),
        (_payload(), (), "bridge_protocol_error"),
        (_payload(), (7, 7), "bridge_protocol_error"),
    ],
)
def test_company_context_payload_and_allowlist_are_fail_closed(
    payload: dict, available_company_ids: tuple[int, ...], code: str
) -> None:
    with pytest.raises(RuntimeFailure) as caught:
        runtime._dispatch(
            _Environment([]),
            "res.company.accounting_context.read_page",
            payload,
            7,
            available_company_ids,
        )

    assert caught.value.code == code
