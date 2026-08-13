from __future__ import annotations

import io
import json
import sys
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

from odoo_accounting_cli_v4.bridge import runtime
from odoo_accounting_cli_v4.bridge.runtime import RuntimeFailure


SEARCH_ACTION = "account.move.journal_entry.search_page"
GET_ACTION = "account.move.journal_entry.get"

MOVE_FIELDS = [
    "id",
    "name",
    "date",
    "state",
    "ref",
    "journal_id",
    "company_id",
    "company_currency_id",
    "partner_id",
]
SEARCH_LINE_FIELDS = ["id", "move_id", "debit", "credit", "balance"]
GET_LINE_FIELDS = [
    "id",
    "move_id",
    "sequence",
    "display_type",
    "name",
    "account_id",
    "partner_id",
    "debit",
    "credit",
    "balance",
    "company_currency_id",
    "amount_currency",
    "currency_id",
    "date_maturity",
    "reconciled",
    "matching_number",
]


def _filters(**overrides: Any) -> dict[str, Any]:
    value = {
        "date_from": None,
        "date_to": None,
        "states": [],
        "journal_id": None,
        "partner_id": None,
        "query": None,
    }
    value.update(overrides)
    return value


def _bridge_request(action: str, payload: dict[str, Any]) -> str:
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
            "action": action,
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
        self.calls.append(
            ("search", self.name, domain, fields, limit, order)
        )
        return [dict(row) for row in self.rows]


class _Companies:
    def __init__(self, calls: list[tuple[Any, ...]], *, visible: bool) -> None:
        self.calls = calls
        self.visible = visible

    def search_count(self, domain: list[Any], *, limit: int) -> int:
        self.calls.append(("company", domain, limit))
        return int(self.visible)


class _Registry:
    def __init__(
        self,
        calls: list[tuple[Any, ...]],
        models: dict[str, Any],
        *,
        installed: bool,
    ) -> None:
        self.calls = calls
        self.models = models
        self.installed = installed

    def get(self, model: str):
        self.calls.append(("registry", model))
        if not self.installed and model in {"account.move", "account.move.line"}:
            return None
        return self.models.get(model)


class _Environment:
    uid = 42

    def __init__(
        self,
        *,
        mode: str,
        company_visible: bool = True,
        installed: bool = True,
        move_access: bool = True,
        line_access: bool = True,
    ) -> None:
        self.calls: list[tuple[Any, ...]] = []
        move = {
            "id": 99,
            "name": "MISC/2025/0001" if mode == "search" else False,
            "date": "2025-01-15",
            "state": "posted" if mode == "search" else "draft",
            "ref": False,
            "journal_id": [5, "MISC Miscellaneous Operations"],
            "company_id": [7, "V4 Company"],
            "company_currency_id": [6, "CNY"],
            "partner_id": [12, "ACME display"] if mode == "search" else False,
        }
        if mode == "search":
            lines = [
                {
                    "id": 501,
                    "move_id": [99, "MISC/2025/0001"],
                    "debit": -1.25,
                    "credit": 0.0,
                    "balance": -1.25,
                },
                {
                    "id": 502,
                    "move_id": [99, "MISC/2025/0001"],
                    "debit": 0.0,
                    "credit": -1.25,
                    "balance": 1.25,
                },
            ]
        else:
            lines = [
                {
                    "id": 501,
                    "move_id": [99, False],
                    "sequence": 10,
                    "display_type": False,
                    "name": False,
                    "account_id": [8, "1010 Cash"],
                    "partner_id": False,
                    "debit": -1.25,
                    "credit": 0.0,
                    "balance": -1.25,
                    "company_currency_id": [6, "CNY"],
                    "amount_currency": -1.25,
                    "currency_id": [6, "CNY"],
                    "date_maturity": False,
                    "reconciled": False,
                    "matching_number": False,
                },
                {
                    "id": 502,
                    "move_id": [99, False],
                    "sequence": 20,
                    "display_type": "line_note",
                    "name": "memo",
                    "account_id": False,
                    "partner_id": False,
                    "debit": 0.0,
                    "credit": 0.0,
                    "balance": 0.0,
                    "company_currency_id": [6, "CNY"],
                    "amount_currency": 0.0,
                    "currency_id": False,
                    "date_maturity": False,
                    "reconciled": False,
                    "matching_number": False,
                },
            ]
        self.models: dict[str, Any] = {
            "res.company": _Companies(self.calls, visible=company_visible),
            "account.move": _Model(
                "account.move", self.calls, [move], access_allowed=move_access
            ),
            "account.move.line": _Model(
                "account.move.line",
                self.calls,
                lines,
                access_allowed=line_access,
            ),
            "account.journal": _Model(
                "account.journal",
                self.calls,
                [{"id": 5, "code": "MISC", "name": "Miscellaneous Operations"}],
            ),
            "res.currency": _Model(
                "res.currency", self.calls, [{"id": 6, "name": "CNY"}]
            ),
            "res.partner": _Model(
                "res.partner",
                self.calls,
                [{"id": 12, "complete_name": "ACME Ltd"}],
            ),
            "account.account": _Model(
                "account.account",
                self.calls,
                [{"id": 8, "code": "1010", "name": "Cash"}],
            ),
        }
        self.registry = _Registry(
            self.calls, self.models, installed=installed
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


def test_decode_accepts_only_the_two_fixed_journal_entry_actions() -> None:
    search_payload = {
        "company_id": 7,
        "after": None,
        "limit": 3,
        "filters": _filters(),
    }
    get_payload = {"company_id": 7, "move_id": 99}

    assert runtime._decode_request(
        io.StringIO(_bridge_request(SEARCH_ACTION, search_payload))
    )["action"] == SEARCH_ACTION
    assert runtime._decode_request(
        io.StringIO(_bridge_request(GET_ACTION, get_payload))
    )["action"] == GET_ACTION


def test_search_uses_fixed_scope_filters_desc_cursor_and_signed_line_totals() -> None:
    env = _Environment(mode="search")
    payload = {
        "company_id": 7,
        "after": ["2025-01-15", 100],
        "limit": 3,
        "filters": _filters(
            date_from="2025-01-01",
            date_to="2025-01-31",
            states=["draft", "posted"],
            journal_id=5,
            partner_id=12,
            query="needle",
        ),
    }

    result = runtime._dispatch(env, SEARCH_ACTION, payload, 7)

    assert result == {
        "user_id": 42,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "rows": [
            {
                "id": 99,
                "name": "MISC/2025/0001",
                "date": "2025-01-15",
                "state": "posted",
                "ref": None,
                "journal": {
                    "id": 5,
                    "code": "MISC",
                    "name": "Miscellaneous Operations",
                },
                "company_id": 7,
                "currency": {"id": 6, "code": "CNY"},
                "partner": {"id": 12, "name": "ACME Ltd"},
                "debit": "-1.25",
                "credit": "-1.25",
                "balance": "0",
            }
        ],
    }
    move_search = _search_call(env, "account.move")
    assert move_search[3:] == (MOVE_FIELDS, 3, "date desc,id desc")
    domain = move_search[2]
    for term in (
        ("company_id", "=", 7),
        ("move_type", "=", "entry"),
        ("date", ">=", "2025-01-01"),
        ("date", "<=", "2025-01-31"),
        ("state", "in", ["draft", "posted"]),
        ("journal_id", "=", 5),
        ("partner_id", "=", 12),
        ("name", "ilike", "needle"),
        ("ref", "ilike", "needle"),
        ("date", "<", "2025-01-15"),
        ("date", "=", "2025-01-15"),
        ("id", "<", 100),
    ):
        assert term in domain
    assert domain.index(("name", "ilike", "needle")) > domain.index("|")
    assert domain[-5:] == [
        "|",
        ("date", "<", "2025-01-15"),
        "&",
        ("date", "=", "2025-01-15"),
        ("id", "<", 100),
    ]
    line_search = _search_call(env, "account.move.line")
    assert line_search[2] == [("move_id", "in", [99])]
    assert line_search[3] == SEARCH_LINE_FIELDS
    assert line_search[5] == "move_id,id"


def test_get_reads_header_and_complete_lines_in_one_dispatch() -> None:
    env = _Environment(mode="get")

    result = runtime._dispatch(
        env, GET_ACTION, {"company_id": 7, "move_id": 99}, 7
    )

    assert result == {
        "user_id": 42,
        "company_visible": True,
        "module_installed": True,
        "access_allowed": True,
        "entry": {
            "id": 99,
            "name": None,
            "date": "2025-01-15",
            "state": "draft",
            "ref": None,
            "journal": {
                "id": 5,
                "code": "MISC",
                "name": "Miscellaneous Operations",
            },
            "company_id": 7,
            "currency": {"id": 6, "code": "CNY"},
            "partner": None,
            "lines": [
                {
                    "id": 501,
                    "sequence": 10,
                    "display_type": None,
                    "name": None,
                    "account": {"id": 8, "code": "1010", "name": "Cash"},
                    "partner": None,
                    "debit": "-1.25",
                    "credit": "0",
                    "balance": "-1.25",
                    "company_currency": {"id": 6, "code": "CNY"},
                    "amount_currency": "-1.25",
                    "currency": {"id": 6, "code": "CNY"},
                    "date_maturity": None,
                    "reconciled": False,
                    "matching_number": None,
                },
                {
                    "id": 502,
                    "sequence": 20,
                    "display_type": "line_note",
                    "name": "memo",
                    "account": None,
                    "partner": None,
                    "debit": "0",
                    "credit": "0",
                    "balance": "0",
                    "company_currency": {"id": 6, "code": "CNY"},
                    "amount_currency": "0",
                    "currency": None,
                    "date_maturity": None,
                    "reconciled": False,
                    "matching_number": None,
                },
            ],
            "totals": {"debit": "-1.25", "credit": "0", "balance": "-1.25"},
        },
    }
    move_search = _search_call(env, "account.move")
    assert move_search[2] == [
        ("id", "=", 99),
        ("company_id", "=", 7),
        ("move_type", "=", "entry"),
    ]
    assert move_search[3] == MOVE_FIELDS
    assert move_search[4] == 1
    line_search = _search_call(env, "account.move.line")
    assert line_search[2] == [("move_id", "=", 99)]
    assert line_search[3] == GET_LINE_FIELDS
    assert line_search[5] == "sequence,id"


@pytest.mark.parametrize(
    ("company_visible", "installed", "move_access", "line_access", "expected"),
    (
        (False, True, True, True, (False, True, False)),
        (True, False, True, True, (True, False, False)),
        (True, True, False, True, (True, True, False)),
        (True, True, True, False, (True, True, False)),
    ),
)
def test_search_gates_company_module_and_both_acls_before_any_read(
    company_visible: bool,
    installed: bool,
    move_access: bool,
    line_access: bool,
    expected: tuple[bool, bool, bool],
) -> None:
    env = _Environment(
        mode="search",
        company_visible=company_visible,
        installed=installed,
        move_access=move_access,
        line_access=line_access,
    )

    result = runtime._dispatch(
        env,
        SEARCH_ACTION,
        {"company_id": 7, "after": None, "limit": 3, "filters": _filters()},
        7,
    )

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
        {
            "company_id": 7,
            "after": None,
            "limit": 3,
            "filters": {**_filters(), "model": "res.users"},
        },
        {
            "company_id": 7,
            "after": ["2025-1-1", 9],
            "limit": 3,
            "filters": _filters(),
        },
        {
            "company_id": 7,
            "after": ["2025-01-01", True],
            "limit": 3,
            "filters": _filters(),
        },
        {
            "company_id": 7,
            "after": None,
            "limit": 3,
            "filters": _filters(states=["posted", "draft"]),
        },
        {
            "company_id": 7,
            "after": None,
            "limit": 3,
            "filters": _filters(query=" needle "),
        },
        {
            "company_id": 7,
            "after": None,
            "limit": 3,
            "filters": _filters(query="x" * 201),
        },
    ),
)
def test_search_payload_and_filters_fail_closed(payload: dict[str, Any]) -> None:
    with pytest.raises(RuntimeFailure) as caught:
        runtime._dispatch(_Environment(mode="search"), SEARCH_ACTION, payload, 7)

    assert caught.value.code == "bridge_protocol_error"
    assert caught.value.exit_code == 7


@pytest.mark.parametrize(
    "payload",
    (
        {"company_id": 7},
        {"company_id": 7, "move_id": 0},
        {"company_id": 7, "move_id": True},
        {"company_id": 7, "move_id": 99, "model": "res.users"},
    ),
)
def test_get_payload_fails_closed(payload: dict[str, Any]) -> None:
    with pytest.raises(RuntimeFailure) as caught:
        runtime._dispatch(_Environment(mode="get"), GET_ACTION, payload, 7)

    assert caught.value.code == "bridge_protocol_error"
    assert caught.value.exit_code == 7


@pytest.mark.parametrize(
    ("action", "payload"),
    (
        (
            SEARCH_ACTION,
            {"company_id": 8, "after": None, "limit": 3, "filters": _filters()},
        ),
        (GET_ACTION, {"company_id": 8, "move_id": 99}),
    ),
)
def test_journal_entry_company_mismatch_fails_closed(
    action: str, payload: dict[str, Any]
) -> None:
    with pytest.raises(RuntimeFailure) as caught:
        runtime._dispatch(_Environment(mode="search"), action, payload, 7)

    assert caught.value.code == "company_unavailable"
    assert caught.value.exit_code == 3


def test_unknown_journal_entry_action_fails_closed_without_model_access() -> None:
    class Environment:
        registry = object()

        def __getitem__(self, model: str):
            raise AssertionError(f"unknown action must not access {model}")

    with pytest.raises(RuntimeFailure) as caught:
        runtime._dispatch(
            Environment(),
            "account.move.journal_entry.arbitrary",
            {"company_id": 7, "move_id": 99},
            7,
        )

    assert caught.value.code == "bridge_protocol_error"
    assert caught.value.exit_code == 7
