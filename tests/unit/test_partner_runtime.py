from __future__ import annotations

import io
import json
import sys
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge import runtime
from odoo_accounting_cli_v4.bridge.runtime import RuntimeFailure


ACTION = "res.partner.accounting.search_page"
PARTNER_FIELDS = [
    "id",
    "complete_name",
    "ref",
    "active",
    "is_company",
    "company_id",
    "customer_rank",
    "supplier_rank",
    "property_account_receivable_id",
    "property_account_payable_id",
]
ACCOUNT_FIELDS = ["id", "code", "name"]


def _filters(**overrides: Any) -> dict[str, Any]:
    value = {"role": "both", "query": None}
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


def _bridge_request(payload: dict[str, Any]) -> str:
    return json.dumps(
        {
            "schema_version": "v1",
            "target": {
                "alias": "v4-dev",
                "database": "odoo_cli_v4_dev",
                "company_id": 7,
                "user_login": "v4-agent",
                "language": "zh_CN",
                "timezone": "Asia/Shanghai",
            },
            "action": ACTION,
            "payload": payload,
        }
    )


@pytest.fixture(autouse=True)
def _fake_odoo_expression(monkeypatch: pytest.MonkeyPatch) -> None:
    def and_domains(domains: list[list[Any]]) -> list[Any]:
        nonempty = [domain for domain in domains if domain]
        result: list[Any] = ["&"] * max(0, len(nonempty) - 1)
        for domain in nonempty:
            result.extend(domain)
        return result

    odoo = ModuleType("odoo")
    odoo.__path__ = []  # type: ignore[attr-defined]
    osv = ModuleType("odoo.osv")
    osv.expression = SimpleNamespace(AND=and_domains)  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "odoo", odoo)
    monkeypatch.setitem(sys.modules, "odoo.osv", osv)


class _Model:
    def __init__(
        self,
        name: str,
        calls: list[tuple[Any, ...]],
        rows: list[dict[str, Any]],
        *,
        access_allowed: bool = True,
    ) -> None:
        self.name = name
        self.calls = calls
        self.rows = rows
        self.access_allowed = access_allowed

    def has_access(self, operation: str) -> bool:
        self.calls.append(("access", self.name, operation))
        return self.access_allowed

    def with_context(self, **context: Any):
        self.calls.append(("context", self.name, context))
        return self

    def search_read(
        self,
        domain: list[Any],
        *,
        fields: list[str],
        limit: int | None = None,
        order: str | None = None,
    ) -> list[dict[str, Any]]:
        self.calls.append(("search", self.name, domain, fields, limit, order))
        return [dict(row) for row in self.rows]

    def sudo(self):
        raise AssertionError(f"{self.name} must never be read with sudo")


class _Companies:
    def __init__(self, calls: list[tuple[Any, ...]], *, visible: bool) -> None:
        self.calls = calls
        self.visible = visible

    def search_count(self, domain: list[Any], *, limit: int) -> int:
        self.calls.append(("company", domain, limit))
        return int(self.visible)

    def sudo(self):
        raise AssertionError("res.company must never be read with sudo")


class _Registry:
    def __init__(
        self,
        calls: list[tuple[Any, ...]],
        models: dict[str, Any],
        *,
        missing_models: set[str],
    ) -> None:
        self.calls = calls
        self.models = models
        self.missing_models = missing_models

    def get(self, model: str):
        self.calls.append(("registry", model))
        if model in self.missing_models:
            return None
        return self.models.get(model)


class _Environment:
    uid = 42

    def __init__(
        self,
        *,
        partner_rows: list[dict[str, Any]] | None = None,
        account_rows: list[dict[str, Any]] | None = None,
        company_visible: bool = True,
        missing_models: set[str] | None = None,
        partner_access: bool = True,
        account_access: bool = True,
    ) -> None:
        self.calls: list[tuple[Any, ...]] = []
        if partner_rows is None:
            partner_rows = [
                {
                    "id": 10,
                    "complete_name": "Alpha Shared",
                    "ref": False,
                    "active": True,
                    "is_company": False,
                    "company_id": False,
                    "customer_rank": 2,
                    "supplier_rank": 1,
                    "property_account_receivable_id": [
                        121,
                        "112200 Accounts Receivable",
                    ],
                    "property_account_payable_id": [
                        221,
                        "220200 Accounts Payable",
                    ],
                }
            ]
        if account_rows is None:
            account_rows = [
                {"id": 121, "code": "112200", "name": "Accounts Receivable"},
                {"id": 221, "code": "220200", "name": "Accounts Payable"},
            ]
        self.models: dict[str, Any] = {
            "res.company": _Companies(self.calls, visible=company_visible),
            "res.partner": _Model(
                "res.partner",
                self.calls,
                partner_rows,
                access_allowed=partner_access,
            ),
            "account.account": _Model(
                "account.account",
                self.calls,
                account_rows,
                access_allowed=account_access,
            ),
        }
        self.registry = _Registry(
            self.calls,
            self.models,
            missing_models=missing_models or set(),
        )

    def __getitem__(self, model: str):
        self.calls.append(("model", model))
        if model not in self.models:
            raise AssertionError(f"unexpected generic model access: {model}")
        return self.models[model]


def _search_call(env: _Environment, model: str) -> tuple[Any, ...]:
    matches = [
        call for call in env.calls if call[0] == "search" and call[1] == model
    ]
    assert len(matches) == 1
    return matches[0]


def test_decode_accepts_the_fixed_partner_accounting_action() -> None:
    assert runtime._decode_request(io.StringIO(_bridge_request(_payload())))[
        "action"
    ] == ACTION


def test_search_uses_fixed_scope_role_query_cursor_and_related_account_reads() -> None:
    env = _Environment()
    payload = _payload(
        after=["Alpha", 9],
        filters=_filters(query="needle"),
    )

    result = runtime._dispatch(env, ACTION, payload, 7)

    assert result == {
        "user_id": 42,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "rows": [
            {
                "id": 10,
                "complete_name": "Alpha Shared",
                "ref": None,
                "active": True,
                "is_company": False,
                "company_id": None,
                "customer_rank": 2,
                "supplier_rank": 1,
                "receivable_account": {
                    "id": 121,
                    "code": "112200",
                    "name": "Accounts Receivable",
                },
                "payable_account": {
                    "id": 221,
                    "code": "220200",
                    "name": "Accounts Payable",
                },
            }
        ],
    }
    partner_search = _search_call(env, "res.partner")
    assert partner_search[2] == [
        "&",
        "&",
        "&",
        "|",
        ("company_id", "=", False),
        ("company_id", "=", 7),
        "|",
        ("customer_rank", ">", 0),
        ("supplier_rank", ">", 0),
        "|",
        ("complete_name", "ilike", "needle"),
        ("ref", "ilike", "needle"),
        "|",
        ("complete_name", ">", "Alpha"),
        "&",
        ("complete_name", "=", "Alpha"),
        ("id", ">", 9),
    ]
    assert partner_search[3:] == (
        PARTNER_FIELDS,
        3,
        "complete_name,id",
    )
    account_search = _search_call(env, "account.account")
    assert account_search[2:] == (
        [("id", "in", [121, 221])],
        ACCOUNT_FIELDS,
        2,
        "id",
    )
    assert (
        "context",
        "res.partner",
        {"active_test": False, "allowed_company_ids": [7]},
    ) in env.calls
    assert (
        "context",
        "account.account",
        {"active_test": False, "allowed_company_ids": [7]},
    ) in env.calls
    assert {
        call for call in env.calls if call[0] == "access"
    } == {
        ("access", "res.partner", "read"),
        ("access", "account.account", "read"),
    }


@pytest.mark.parametrize(
    ("role", "expected_role_domain"),
    (
        ("customer", [("customer_rank", ">", 0)]),
        ("vendor", [("supplier_rank", ">", 0)]),
        (
            "both",
            [
                "|",
                ("customer_rank", ">", 0),
                ("supplier_rank", ">", 0),
            ],
        ),
    ),
)
def test_role_filters_are_fixed(
    role: str, expected_role_domain: list[Any]
) -> None:
    env = _Environment(partner_rows=[])

    runtime._dispatch(
        env,
        ACTION,
        _payload(filters=_filters(role=role)),
        7,
    )

    assert _search_call(env, "res.partner")[2] == [
        "&",
        "|",
        ("company_id", "=", False),
        ("company_id", "=", 7),
        *expected_role_domain,
    ]


def test_non_null_property_account_must_resolve_to_the_fixed_related_read() -> None:
    env = _Environment(
        account_rows=[
            {"id": 121, "code": "112200", "name": "Accounts Receivable"}
        ]
    )

    with pytest.raises(RuntimeFailure) as caught:
        runtime._dispatch(env, ACTION, _payload(), 7)

    assert caught.value.code == "odoo_runtime_error"
    assert caught.value.exit_code == 7


@pytest.mark.parametrize(
    (
        "company_visible",
        "missing_models",
        "partner_access",
        "account_access",
        "expected",
    ),
    (
        (False, set(), True, True, (False, True, False)),
        (True, {"res.partner"}, True, True, (True, False, False)),
        (True, {"account.account"}, True, True, (True, False, False)),
        (True, set(), False, True, (True, True, False)),
        (True, set(), True, False, (True, True, False)),
    ),
)
def test_company_module_and_both_acl_gates_stop_before_any_business_read(
    company_visible: bool,
    missing_models: set[str],
    partner_access: bool,
    account_access: bool,
    expected: tuple[bool, bool, bool],
) -> None:
    env = _Environment(
        company_visible=company_visible,
        missing_models=missing_models,
        partner_access=partner_access,
        account_access=account_access,
    )

    result = runtime._dispatch(env, ACTION, _payload(), 7)

    assert (
        result["company_visible"],
        result["module_installed"],
        result["access_allowed"],
    ) == expected
    assert result["rows"] == []
    assert not any(call[0] in {"context", "search"} for call in env.calls)


@pytest.mark.parametrize(
    "payload",
    (
        {"company_id": 7, "after": None, "limit": 3},
        {**_payload(), "model": "res.users"},
        _payload(after=["", 9]),
        _payload(after=["Alpha", True]),
        _payload(limit=True),
        _payload(limit=1002),
        _payload(filters={**_filters(), "domain": []}),
        _payload(filters=_filters(role="CUSTOMER")),
        _payload(filters=_filters(role="invalid")),
        _payload(filters=_filters(query=" needle")),
        _payload(filters=_filters(query="")),
        _payload(filters=_filters(query="x" * 201)),
    ),
)
def test_payload_and_filters_fail_closed(payload: dict[str, Any]) -> None:
    env = _Environment()

    with pytest.raises(RuntimeFailure) as caught:
        runtime._dispatch(env, ACTION, payload, 7)

    assert caught.value.code == "bridge_protocol_error"
    assert caught.value.exit_code == 7
    assert not any(call[0] in {"model", "context", "search"} for call in env.calls)


def test_company_mismatch_fails_closed_before_model_access() -> None:
    env = _Environment()

    with pytest.raises(RuntimeFailure) as caught:
        runtime._dispatch(env, ACTION, _payload(company_id=8), 7)

    assert caught.value.code == "company_unavailable"
    assert caught.value.exit_code == 3
    assert env.calls == []


def test_unknown_partner_action_fails_closed_without_model_access() -> None:
    class Environment:
        registry = object()

        def __getitem__(self, model: str):
            raise AssertionError(f"unknown action must not access {model}")

    with pytest.raises(RuntimeFailure) as caught:
        runtime._dispatch(
            Environment(),
            "res.partner.accounting.arbitrary",
            _payload(),
            7,
        )

    assert caught.value.code == "bridge_protocol_error"
    assert caught.value.exit_code == 7
